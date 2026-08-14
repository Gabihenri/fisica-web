import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'br.com.edudata.fisicaweb',
  appName: 'Física Web',
  webDir: 'www',
  bundledWebRuntime: false,
  server: {
    url: 'https://fisica-web.onrender.com',
    cleartext: false,
    allowNavigation: ['fisica-web.onrender.com']
  },
  android: {
    allowMixedContent: false
  },
  ios: {
    contentInset: 'automatic'
  }
};

export default config;
