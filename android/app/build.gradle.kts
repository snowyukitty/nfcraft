plugins {
    id("com.android.application")
}

android {
    namespace = "best.tgs.cardwriter"
    compileSdk = 36

    defaultConfig {
        applicationId = "best.tgs.cardwriter"
        minSdk = 21
        targetSdk = 36
        versionCode = 8
        versionName = "0.5.1"
    }

    val signingValues = listOf("NFCRAFT_UPLOAD_STORE_FILE", "NFCRAFT_UPLOAD_STORE_PASSWORD",
        "NFCRAFT_UPLOAD_KEY_ALIAS", "NFCRAFT_UPLOAD_KEY_PASSWORD").map { System.getenv(it) }
    require(signingValues.all { it.isNullOrBlank() } || signingValues.all { !it.isNullOrBlank() }) {
        "Set all four NFCRAFT_UPLOAD_* signing variables, or leave all unset for an unsigned preparation build."
    }
    if (signingValues.all { !it.isNullOrBlank() }) {
        signingConfigs.create("upload") {
            storeFile = file(signingValues[0]!!)
            storePassword = signingValues[1]
            keyAlias = signingValues[2]
            keyPassword = signingValues[3]
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            if (signingConfigs.findByName("upload") != null) {
                signingConfig = signingConfigs.getByName("upload")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.robolectric:robolectric:4.16.1")
}
