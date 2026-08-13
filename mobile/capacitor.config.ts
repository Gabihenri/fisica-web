import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'br.com.edudata.fisicaweb',
  appName: 'Física Web',
  webDir: 'www',
  bundledWebRuntime: false,
  android: {
    allowMixedContent: false
  },
  ios: {
    contentInset: 'automatic'
  }
};

export default config;
