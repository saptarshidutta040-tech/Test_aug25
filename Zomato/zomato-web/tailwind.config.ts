import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'background':                '#0a0e1a',
        'surface':                   '#0f1524',
        'surface-container':         '#141c2e',
        'surface-container-high':    '#1a2438',
        'surface-container-highest': '#202c42',
        'surface-variant':           '#1a2438',
        'on-surface':                '#e0e8f0',
        'on-surface-variant':        '#a0b4c4',
        'on-background':             '#e0e8f0',
        'primary':                   '#7dd3fc',
        'primary-container':         '#0e4d6e',
        'on-primary':                '#001f2e',
        'on-primary-container':      '#c8eaff',
        'secondary':                 '#88b4cc',
        'secondary-container':       '#1a3a4e',
        'on-secondary-container':    '#c0d8e8',
        'tertiary':                  '#c8a0f0',
        'tertiary-container':        '#3d2060',
        'on-tertiary-container':     '#e8d0ff',
        'error':                     '#ff6b6b',
        'error-container':           '#3d1414',
        'on-error-container':        '#ffb3b3',
        'outline':                   '#4a6070',
        'outline-variant':           '#2a3a48',
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '1rem',
        xl: '1.5rem',
        full: '9999px',
      },
      spacing: {
        xs: '4px',
        sm: '12px',
        base: '8px',
        md: '24px',
        gutter: '16px',
        lg: '40px',
        xl: '64px',
        'container-margin': '20px',
      },
      fontFamily: {
        headline: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        label: ['Inter', 'sans-serif'],
      },
      fontSize: {
        'body-md':          ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'body-lg':          ['18px', { lineHeight: '28px', fontWeight: '400' }],
        'label-sm':         ['12px', { lineHeight: '16px', letterSpacing: '0.05em', fontWeight: '700' }],
        'label-md':         ['14px', { lineHeight: '20px', letterSpacing: '0.01em', fontWeight: '500' }],
        'headline-md':      ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'headline-lg':      ['32px', { lineHeight: '40px', letterSpacing: '-0.01em', fontWeight: '700' }],
        'headline-xl':      ['40px', { lineHeight: '48px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-lg-mobile': ['28px', { lineHeight: '36px', fontWeight: '700' }],
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};

export default config;
