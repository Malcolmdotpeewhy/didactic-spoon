# LeagueLoop Mobile: Play Store Release Guide

In order to sell this Android companion app on the Google Play Store, you need to compile the code into a signed **Android App Bundle (.aab)**. 

Google requires all production apps to be digitally signed with a keystore before they can be uploaded. Here is exactly how to do that step-by-step.

## Prerequisites
1. **Java JDK 17+** (Required to use `keytool` and Gradle)
2. **Android Studio SDK** (Required to compile android projects)

## 1. Create a Keystore
You only need to do this **once**. This keystore acts as the signature identifying you as the author. Do not lose this file!

Open a terminal in the `LeagueLoopMobile` directory and run:
**(Windows)**
```powershell
keytool -genkey -v -keystore release.keystore -alias leagueloop_alias -keyalg RSA -keysize 2048 -validity 10000
```
It will ask for a password. Remember this password. It will generate a file named `release.keystore`. 

## 2. Generate the Unsigned Binaries
Double click the `build_android.bat` file we provided. 
This will compile the Vite frontend, copy the assets to Capacitor, and run Gradle to generate the raw bundles:
- **APK**: `android/app/build/outputs/apk/release/app-release-unsigned.apk`
- **AAB**: `android/app/build/outputs/bundle/release/app-release.aab`

*The AAB is strictly for the Play Store. The APK is for you to test on your own device outside of the app store.*

## 3. Sign the AAB (Ready for Delivery)
To sign the App Bundle, use `jarsigner` (part of the Java JDK).

```powershell
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 -keystore release.keystore android\app\build\outputs\bundle\release\app-release.aab leagueloop_alias
```

## 4. Upload to Google Play Console
1. Create a [Google Play Developer Account](https://play.google.com/console).
2. Click **Create App** and fill in your store details (Name, Short Description, Pricing).
3. Go to **Production** -> **Create new release**.
4. Upload the signed `app-release.aab` file you just generated.
5. Provide screenshots of the App.

## 5. Changing the App Icon
By default, Capacitor uses the generic Capacitor logo. To use your own logo:
1. Replace `assets/logo.png` inside the android folder.
2. The fastest way to generate all Android icon sizes perfectly is by installing `@capacitor/assets`:
   ```bash
   npm install @capacitor/assets --save-dev
   npx capacitor-assets generate --android
   ```
   *Note: Just drop your high-res `icon.png` (1024x1024) into a folder called `assets/` in your root project before running it.*
