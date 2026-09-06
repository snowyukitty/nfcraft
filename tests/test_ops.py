from __future__ import annotations
import csv, io, json, sqlite3, tempfile, threading, time, unittest
from dataclasses import replace
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from nfcraft.ndef import *
from nfcraft.errors import OpsError
from nfcraft.adapters.mock import MockReader
from nfcraft.adapters.pcsc import Acs1552Reader, parse_objects
from nfcraft.store import Store
from nfcraft.engine import Engine
from nfcraft.exporting import inventory_csv, manifest_sql
from nfcraft.server import LocalServer
from nfcraft.mcp import dispatch, serve, TOOLS
from nfcraft.runtime import WorkspaceLock

class NdefTests(unittest.TestCase):
    def test_known_vector(self):
        self.assertEqual(uri_record('https://a.co').hex(), 'd101055504612e636f')
    def test_round_trip(self):
        for u in ('https://example.com', 'https://tap.example.com/c/'+'A'*22, 'https://xn--fiqs8s.cn/%E7%8C%AB'):
            with self.subTest(u=u): self.assertEqual(decode_area(encode_area(u)),u)
    def test_496_not_504(self):
        self.assertEqual(NDEF_CAPACITY,496); self.assertEqual(CC,bytes.fromhex('e1103e00'))
    def test_short_url_limit(self):
        u='https://a.co/'+('x'*187)
        self.assertEqual(len(u),200); self.assertEqual(decode_area(encode_area(u)),u)
        with self.assertRaises(OpsError): encode_area(u+'x')
    def test_invalid_urls(self):
        for u in ('http://example.com','https://user:pass@example.com','https://example.com/#x','https://ex ample.com','https://例子.cn','https://example.com\\x','https://bad..com','https://-bad.com','https://a-.com','https://x.com:abc','https://x.com\n','javascript:alert(1)'):
            with self.subTest(u=u),self.assertRaises(OpsError): validate_https(u)
    def test_real_base_rejects_placeholders(self):
        for host in ('example.com','tap.example.net','localhost','127.0.0.1','a.local','a.test','x.invalid'):
            with self.subTest(host=host),self.assertRaises(OpsError): validate_base('https://'+host,production=True)
    def test_real_base_accepts_dns(self):
        self.assertEqual(validate_base('https://cards.my-owned-domain.com/',production=True),'https://cards.my-owned-domain.com')
    def test_base_rejects_path_query_nonstandard_port(self):
        for b in ('https://cards.testdomain.com/c','https://cards.testdomain.com?x','https://cards.testdomain.com:47821',None):
            with self.subTest(b=b),self.assertRaises(OpsError): validate_base(b,production=True)
    def test_commit_last(self):
        p=write_plan('https://example.com/c/'+'B'*22)
        self.assertEqual(p[0][0],4); self.assertEqual(p[0][1][1],0)
        self.assertEqual(p[-1][0],4); self.assertGreater(p[-1][1][1],0)
        for page,data in p: assert_safe_page(page,data)
    def test_pages_restricted(self):
        for page in list(range(4))+list(range(128,256))+[-1,True]:
            with self.subTest(page=page),self.assertRaises(OpsError): assert_safe_page(page,b'1234')
    def test_alignment(self):
        for n in range(1,170): self.assertEqual(len(encode_area('https://a.co/'+'x'*n))%4,0)
    def test_wrong_page_size(self):
        for data in (b'',b'123',b'12345'):
            with self.assertRaises(OpsError): assert_safe_page(4,data)
    def test_noncanonical_decode(self):
        for d in (b'',bytes(496),b'\x03\xff'+bytes(494),b'\x03\x00\xfe',b'\x03\x06\xd1\x01\x02U\x04x'):
            self.assertIsNone(decode_area(d))
    def test_empty_format(self):
        self.assertTrue(is_empty(bytes(496))); self.assertTrue(is_empty(b'\x03\x00\xfe'+bytes(493)))
        self.assertFalse(is_empty(bytes(504)));self.assertFalse(is_empty(b'other'+bytes(491)))
    def test_recovery_whole_pages_only(self):
        original=b'\x03\x00\xfe\x00'+bytes(492); target=encode_area('https://example.com/c/'+'A'*22)
        current=bytearray(original)
        for page,data in write_plan('https://example.com/c/'+'A'*22):
            i=(page-4)*4; current[i:i+4]=data
            self.assertTrue(recovery_matches(bytes(current),original,target))
        current[7]^=1; self.assertFalse(recovery_matches(bytes(current),original,target))

class Rig(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.path=Path(self.temp.name)
        self.store=Store(self.path/'db.sqlite3'); self.reader=MockReader(self.path/'tags'); self.engine=Engine(self.store,self.reader)
    def tearDown(self):
        self.engine.shutdown(); self.temp.cleanup()
    def batch(self,n=10):
        return self.engine.create_batch({'name':'Pilot','target':n,'base':'https://tap.example.com'})
    def arm(self,b,**kw):
        return self.engine.arm({'batch_id':b['id'],'confirmation':'ARM '+b['name'],**kw})
    def provision(self,n=10,scenario='blank'):
        b=self.batch(n); self.arm(b); uid=self.reader.insert(scenario);self.engine.tick();return b,uid

class EngineTests(Rig):
    def test_normal_provision(self):
        _,uid=self.provision(); c=self.store.by_uid(uid)
        self.assertEqual(c['status'],'verified');self.assertEqual(decode_area(self.reader.read_area()),c['url'])
        self.assertEqual(len(c['slug']),22);self.assertTrue(self.engine.last['simulated'])
        self.assertTrue(all(4<=p<=127 for p in self.reader.written_pages))
    def test_ten_cards_distinct(self):
        b=self.batch(10);self.arm(b)
        for _ in range(10):
            self.reader.insert();self.engine.tick();self.reader.remove();self.engine.tick()
        cards=self.store.inventory(); self.assertEqual(len(cards),10)
        self.assertEqual(len({c['url'] for c in cards}),10);self.assertTrue(all(c['status']=='verified' for c in cards));self.assertIsNone(self.engine.armed)
    def test_held_card_not_reallocated(self):
        _,uid=self.provision();writes=self.reader.write_count
        for _ in range(10):self.engine.tick()
        self.assertEqual(len(self.store.inventory()),1);self.assertEqual(self.reader.write_count,writes)
    def test_duplicate_after_removal_stops(self):
        _,uid=self.provision(); self.reader.remove();self.engine.tick();self.reader.insert(uid=uid);self.engine.tick()
        self.assertEqual(self.engine.last['code'],'DUPLICATE_CARD');self.assertEqual(self.reader.write_count,0);self.assertEqual(len(self.store.inventory()),1)
    def test_draft_does_not_write(self):
        self.batch();self.reader.insert();self.engine.tick();self.assertEqual(self.reader.write_count,0)
    def test_confirmation_required(self):
        b=self.batch()
        with self.assertRaises(OpsError):self.engine.arm({'batch_id':b['id'],'confirmation':'yes'})
    def test_remove_before_arm(self):
        b=self.batch();self.reader.insert()
        with self.assertRaises(OpsError):self.arm(b)
    def test_ttl_expires_without_writing(self):
        b=self.batch();self.arm(b);self.engine.armed['expires']=time.monotonic()-1;self.reader.insert();self.engine.tick()
        self.assertIsNone(self.engine.armed);self.assertEqual(self.reader.write_count,0)
    def test_pause_without_writing(self):
        b=self.batch();self.arm(b);self.engine.pause();self.reader.insert();self.engine.tick();self.assertEqual(self.reader.write_count,0)
    def test_attempt_budget(self):
        b=self.batch();self.arm(b,limit=1);self.reader.insert();self.engine.tick();self.assertIsNone(self.engine.armed)
    def test_invalid_lease(self):
        b=self.batch()
        for kwargs in ({'limit':0},{'limit':True},{'seconds':601},{'seconds':14}):
            with self.subTest(kwargs=kwargs),self.assertRaises(OpsError):self.arm(b,**kwargs)
    def test_foreign_not_overwritten(self):
        _,uid=self.provision(scenario='foreign');self.assertEqual(self.engine.last['code'],'FOREIGN_CONTENT');self.assertEqual(self.reader.write_count,0);self.assertIsNone(self.store.by_uid(uid))
    def test_locked_not_overwritten(self):
        self.provision(scenario='locked');self.assertEqual(self.reader.write_count,0);self.assertEqual(len(self.store.inventory()),0)
    def test_wrong_tag_not_overwritten(self):
        self.provision(scenario='ntag213');self.assertEqual(self.reader.write_count,0);self.assertEqual(len(self.store.inventory()),0)
    def test_unsafe_configuration(self):
        self.reader.insert();i=self.reader.inspect()
        for change in ({'dynamic_locks':'010000'},{'config0':'04000004'},{'config0':'440000ff'},{'config1':'10000000'},{'cc':'e1103e0f'},{'uid':'11223344556677'}):
            with self.subTest(change=change),self.assertRaises(OpsError):replace(i,**change).require_safe()
    def test_interruption_quarantines(self):
        b,uid=self.provision(scenario='interrupted');c=self.store.by_uid(uid)
        self.assertEqual(c['status'],'quarantined');self.assertTrue(c['target_hex']);self.assertIsNone(self.engine.armed);self.assertEqual(len(self.store.manifest()['routes']),0)
    def test_recovery_same_identity(self):
        b,uid=self.provision(scenario='interrupted');before=self.store.by_uid(uid);self.reader.clear_fault()
        self.arm(b,recover_uid=uid);self.engine.tick();after=self.store.by_uid(uid)
        self.assertEqual(after['id'],before['id']);self.assertEqual(after['url'],before['url']);self.assertEqual(after['status'],'verified');self.assertEqual(len(self.store.inventory()),1)
    def test_full_batch_can_recover(self):
        b,uid=self.provision(1,'interrupted');self.reader.clear_fault();self.arm(b,recover_uid=uid);self.engine.tick();self.assertEqual(self.store.by_uid(uid)['status'],'verified')
    def test_no_silent_recovery(self):
        b,uid=self.provision(scenario='interrupted');self.reader.remove();self.arm(b);self.reader.insert(uid=uid);self.engine.tick()
        self.assertEqual(self.engine.last['code'],'RECOVERY_REQUIRED');self.assertEqual(self.reader.write_count,0)
    def test_wrong_recovery_uid(self):
        b,uid=self.provision(scenario='interrupted');self.reader.remove();self.reader.insert();self.arm(b,recover_uid=uid);self.engine.tick()
        self.assertEqual(self.engine.last['code'],'WRONG_RECOVERY_CARD');self.assertEqual(self.reader.write_count,0)
    def test_changed_recovery_data_rejected(self):
        b,uid=self.provision(scenario='interrupted');data=bytearray(self.reader.read_area());data[-1]=99;self.reader.card['area']=data.hex();self.reader.clear_fault()
        self.arm(b,recover_uid=uid);writes=self.reader.write_count;self.engine.tick()
        self.assertEqual(self.engine.last['code'],'RECOVERY_MISMATCH');self.assertEqual(writes,self.reader.write_count)
    def test_readback_mismatch_quarantines(self):
        b=self.batch();self.arm(b);uid=self.reader.insert();original=self.reader.read_area;calls=0
        def altered():
            nonlocal calls
            calls+=1;value=original()
            return value[:-1]+b'\x01' if calls>1 else value
        with patch.object(self.reader,'read_area',side_effect=altered):self.engine.tick()
        self.assertEqual(self.store.by_uid(uid)['status'],'quarantined');self.assertEqual(self.engine.last['code'],'VERIFY_FAILED')
    def test_pause_between_pages_quarantines(self):
        b=self.batch();self.arm(b);uid=self.reader.insert();write=self.reader.write_page
        def stop_after_page(p,d):write(p,d);self.engine.pause_requested.set()
        with patch.object(self.reader,'write_page',side_effect=stop_after_page):self.engine.tick()
        self.assertEqual(self.store.by_uid(uid)['status'],'quarantined');self.assertEqual(self.reader.write_count,1)
    def test_reserved_is_durable_before_write(self):
        b=self.batch();self.arm(b);uid=self.reader.insert();write=self.reader.write_page
        def check_before_write(p,d):
            with closing(sqlite3.connect(self.store.path)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM cards WHERE uid=?',(uid,)).fetchone()[0],1)
            write(p,d)
        with patch.object(self.reader,'write_page',side_effect=check_before_write):self.engine.tick()
        self.assertEqual(self.store.by_uid(uid)['status'],'verified')
    def test_preserves_unused_area(self):
        b=self.batch();self.arm(b);uid=self.reader.insert();area=bytearray(self.reader.read_area());area[-1]=173;self.reader.card['area']=area.hex();self.engine.tick()
        self.assertEqual(self.store.by_uid(uid)['status'],'verified');self.assertEqual(self.reader.read_area()[-1],173)
    def test_reservation_not_recycled_when_batch_full(self):
        b,uid=self.provision(1,'interrupted');self.reader.remove()
        with self.assertRaises(OpsError):self.arm(b)
        self.assertEqual(len(self.store.inventory()),1)
    def test_restart_quarantines_pending(self):
        b=self.batch();uid=self.reader.insert();c=self.store.reserve(b,self.reader.inspect(),self.reader.read_area());self.store.begin_attempt(c)
        self.store.close();self.store=Store(self.path/'db.sqlite3');self.engine=Engine(self.store,self.reader)
        self.assertEqual(self.store.by_uid(uid)['status'],'quarantined');self.assertIsNone(self.engine.armed)
    def test_manifest_has_no_uid(self):
        _,uid=self.provision();m=self.store.manifest();self.assertNotIn(uid,json.dumps(m));self.assertNotIn('uid',json.dumps(m));self.assertTrue(m['simulated'])
    def test_public_state_separate(self):
        self.provision();self.assertIn('Not deployed',self.engine.snapshot()['publication']);self.assertFalse(self.engine.snapshot()['hardware_qualified'])
    def test_suspend_is_only_manifest_intent(self):
        _,uid=self.provision();c=self.store.by_uid(uid);self.store.set_route_state(c['id'],'suspended')
        self.assertEqual(self.store.manifest()['routes'][0]['state'],'suspended');self.assertEqual(self.store.by_uid(uid)['status'],'verified')
    def test_valid_audit_and_corruption_detection(self):
        self.provision();self.assertTrue(self.store.check_audit()['ok'])
        self.store.db.execute("UPDATE audit SET data='{}' WHERE seq=1");self.assertFalse(self.store.check_audit()['ok'])
    def test_corrupt_audit_refuses_arm(self):
        b=self.batch();self.store.db.execute("UPDATE audit SET data='{}' WHERE seq=1")
        with self.assertRaises(OpsError) as error:self.arm(b)
        self.assertEqual(error.exception.code,'AUDIT_INVALID')
    def test_lease_expiring_after_reservation_quarantines(self):
        b=self.batch();self.arm(b);uid=self.reader.insert();reserve=self.store.reserve
        def expired(*args):
            card=reserve(*args);self.engine.armed['expires']=time.monotonic()-1;return card
        with patch.object(self.store,'reserve',side_effect=expired):self.engine.tick()
        self.assertEqual(self.store.by_uid(uid)['status'],'quarantined');self.assertEqual(self.reader.write_count,0)
    def test_backup(self):
        self.provision();p=self.path/'backup.sqlite3';self.store.backup(p)
        with closing(sqlite3.connect(p)) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM cards').fetchone()[0],1)
    def test_demo_sql_guard(self):
        self.provision()
        with self.assertRaises(OpsError):manifest_sql(self.store.manifest())
        sql=manifest_sql(self.store.manifest(),allow_demo=True)
        self.assertIn('INSERT INTO routes',sql)
    def test_profile_sql_escaping(self):
        self.store.update_profile({'name':"O'Neil <script>",'bio':'中文\n日本語'});self.provision();sql=manifest_sql(self.store.manifest(),allow_demo=True)
        with closing(sqlite3.connect(':memory:')) as db:
            db.executescript((Path(__file__).parent.parent/'cloudflare/schema.sql').read_text());db.executescript(sql)
            body=db.execute('SELECT body FROM profiles').fetchone()[0]
            self.assertEqual(json.loads(body)['name'],"O'Neil <script>")
    def test_csv_formula_injection(self):
        text=inventory_csv([{'id':'=1+1','batch_name':'+cmd','url':'https://example.com'}]);rows=list(csv.reader(io.StringIO(text)))
        self.assertIn("'=1+1",rows[1]);self.assertIn("'+cmd",rows[1])
    def test_workspace_mode_guard(self):
        self.store.close()
        with self.assertRaises(OpsError):Store(self.path/'db.sqlite3',mode='hardware')
        self.store=Store(self.path/'db.sqlite3');self.engine=Engine(self.store,self.reader)
    def test_batch_validation(self):
        for n in (0,-1,1001,True,'10'):
            with self.subTest(n=n),self.assertRaises(OpsError):self.batch(n)
    def test_profile_blocks_email_injection(self):
        with self.assertRaises(OpsError):self.store.update_profile({'name':'x','email':'x@a.com\nURL:evil'})

class ServerTests(Rig):
    def setUp(self):
        super().setUp();self.server=LocalServer(self.engine,self.path,0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();super().tearDown()
    def req(self,path,body=None,role='operator',headers=None):
        h={'Authorization':'Bearer '+(self.server.operator_token if role=='operator' else self.server.agent_token)} if role else {}
        if body is not None:h['Content-Type']='application/json'
        h.update(headers or {})
        request=Request(self.server.origin+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
        try:
            with urlopen(request,timeout=3) as r:return r.status,r.read(),r.headers
        except HTTPError as e:return e.code,e.read(),e.headers
    def test_static_csp(self):
        status,body,h=self.req('/',role=None);self.assertEqual(status,200);self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy']);self.assertNotIn(self.server.operator_token.encode(),body)
    def test_api_needs_token(self):self.assertEqual(self.req('/api/state',role=None)[0],401)
    def test_agent_cannot_arm(self):
        b=self.batch();self.assertEqual(self.req('/api/arm',{'batch_id':b['id'],'confirmation':'ARM Pilot'},'agent')[0],403)
    def test_agent_can_prepare_not_arm(self):
        status,body,_=self.req('/api/batches',{'name':'Prepared','target':3,'base':'https://tap.example.com'},'agent')
        self.assertEqual(status,201);self.assertIsNone(self.engine.armed)
    def test_agent_cannot_change_profile(self):self.assertEqual(self.req('/api/profile',{'name':'changed'},'agent')[0],403)
    def test_cross_origin_rejected(self):self.assertEqual(self.req('/api/state',headers={'Origin':'https://attacker.example'})[0],403)
    def test_dns_rebinding_host_rejected(self):self.assertEqual(self.req('/api/state',headers={'Host':'attacker.example'})[0],403)
    def test_mock_operator_action(self):self.assertEqual(self.req('/api/mock/insert',{})[0],200)
    def test_operator_flow(self):
        b=self.batch(1);self.assertEqual(self.req('/api/arm',{'batch_id':b['id'],'confirmation':'ARM Pilot'})[0],200)
        self.req('/api/mock/insert',{});self.engine.tick();status,body,_=self.req('/api/state')
        self.assertEqual(json.loads(body)['cards'][0]['status'],'verified')
    def test_no_raw_or_lock_api(self):
        for p in ('/api/raw-apdu','/api/permanent-lock','/api/erase'):
            self.assertEqual(self.req(p,{},'operator')[0],404)
    def test_unknown_file_not_served(self):self.assertEqual(self.req('/../pyproject.toml')[0],404)

class ProtocolTests(unittest.TestCase):
    def test_pcsc_response_objects(self):
        self.assertEqual(parse_objects(bytes.fromhex('c00300900097020a00'))[0x97],b'\x0a\x00')
    def test_pcsc_rejects_status_truncated_duplicate(self):
        for value in ('c003016300','970100','c003009000970501','c003009000c003009000','c081'):
            with self.subTest(value=value),self.assertRaises(OpsError):parse_objects(bytes.fromhex(value))
    def test_pcsc_default_readonly(self):
        r=Acs1552Reader('ACS ACR1552U PICC 0');self.assertFalse(r.allow_writes)
        with self.assertRaises(OpsError):r.write_page(4,b'1234')
    def test_pcsc_rejects_wrong_reader(self):
        for name in ('ACR122U','ACR1552U SAM','unknown'):
            with self.assertRaises(OpsError):Acs1552Reader(name)
    def test_mcp_initialize(self):
        r=dispatch(None,{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25'}})
        self.assertEqual(r['result']['protocolVersion'],'2025-11-25')
    def test_mcp_no_dangerous_tools(self):
        self.assertFalse(any('arm' in t['name'] or 'lock' in t['name'] or 'raw' in t['name'] for t in TOOLS))
    def test_mcp_no_notification_response(self):self.assertIsNone(dispatch(None,{'jsonrpc':'2.0','method':'notifications/initialized'}))
    def test_mcp_invalid_tool(self):
        r=dispatch(None,{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'nfc_arm','arguments':{}}});self.assertTrue(r['result']['isError'])
    def test_mcp_proxy(self):
        class Client:
            def call(self,path,body):return {'path':path,'body':body}
        r=dispatch(Client(),{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'nfc_batch_create','arguments':{'name':'Pilot','target':10,'base':'https://tap.example.com'}}})
        self.assertEqual(json.loads(r['result']['content'][0]['text'])['path'],'/api/batches')
    def test_mcp_stdio_framing(self):
        source=io.StringIO('bad\n'+json.dumps({'jsonrpc':'2.0','id':1,'method':'ping'})+'\n');sink=io.StringIO();serve(None,source,sink)
        lines=[json.loads(l) for l in sink.getvalue().splitlines()];self.assertEqual(len(lines),2);self.assertEqual(lines[0]['error']['code'],-32700);self.assertEqual(lines[1]['result'],{})

if __name__=='__main__':unittest.main()
