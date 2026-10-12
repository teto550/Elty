import glob
import os
import shutil

from PIL import Image, ImageDraw

APP = 'android/app/src/main'

# 1) Permissions
p = APP + '/AndroidManifest.xml'
s = open(p, encoding='utf-8').read()
perms = ['ACCESS_COARSE_LOCATION', 'ACCESS_FINE_LOCATION', 'ACCESS_BACKGROUND_LOCATION',
         'FOREGROUND_SERVICE', 'FOREGROUND_SERVICE_LOCATION', 'POST_NOTIFICATIONS', 'WAKE_LOCK',
         'REQUEST_IGNORE_BATTERY_OPTIMIZATIONS']
add = ''.join('    <uses-permission android:name="android.permission.%s" />\n' % x for x in perms)
s = s.replace('<application', add + '    <application', 1)
open(p, 'w', encoding='utf-8').write(s)

# 2) Battery plugin + MainActivity
main_path = glob.glob(APP + '/java/**/MainActivity.java', recursive=True)[0]
pkg_dir = os.path.dirname(main_path)
shutil.copy('native/ElityBatteryPlugin.java', pkg_dir + '/ElityBatteryPlugin.java')
open(main_path, 'w', encoding='utf-8').write('''package com.datapulse.elty;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ElityBatteryPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
''')

# 3) Launcher icons from the Elty logo
logo = Image.open('icon-512.png').convert('RGBA')
safe = Image.open('icon-maskable-512.png').convert('RGBA')
legacy = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
fg = {'mdpi': 108, 'hdpi': 162, 'xhdpi': 216, 'xxhdpi': 324, 'xxxhdpi': 432}
for d, size in legacy.items():
    out = '%s/res/mipmap-%s' % (APP, d)
    os.makedirs(out, exist_ok=True)
    logo.resize((size, size), Image.LANCZOS).save(out + '/ic_launcher.png')
    r = safe.resize((size, size), Image.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    r.putalpha(mask)
    r.save(out + '/ic_launcher_round.png')
    safe.resize((fg[d], fg[d]), Image.LANCZOS).save(out + '/ic_launcher_foreground.png')

bg = APP + '/res/values/ic_launcher_background.xml'
open(bg, 'w', encoding='utf-8').write('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#FFFFFF</color>
</resources>
''')
# 4) Fixed signing key (so new builds install over old ones) + increasing versionCode
import re
g = 'android/app/build.gradle'
t = open(g, encoding='utf-8').read()
t = re.sub(r'versionCode\s+\d+', 'versionCode ' + os.environ.get('RUN_NUMBER', '1'), t, count=1)
t += '''

android {
    signingConfigs {
        debug {
            storeFile file('../../signing/elty.keystore')
            storePassword 'eltyfamily2026'
            keyAlias 'elty'
            keyPassword 'eltyfamily2026'
        }
    }
}
'''
open(g, 'w', encoding='utf-8').write(t)
print('android setup done')
