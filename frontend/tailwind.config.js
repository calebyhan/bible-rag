/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['var(--font-crimson-pro)', 'Baskerville', 'Georgia', 'serif'],
        body: ['var(--font-crimson-text)', 'Garamond', 'Georgia', 'serif'],
        korean: ['var(--font-noto-serif-kr)', 'Nanum Myeongjo', 'serif'],
        ui: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'verse': ['20px', { lineHeight: '1.75' }],
        'verse-korean': ['19px', { lineHeight: '2.0' }],
        'reference': ['16px', { lineHeight: '1.5' }],
        'caption': ['14px', { lineHeight: '1.6' }],
      },
      letterSpacing: {
        'korean': '0.02em',
      },
      spacing: {
        'space-xs': '0.5rem',
        'space-sm': '1rem',
        'space-md': '2rem',
        'space-lg': '4rem',
        'space-xl': '6rem',
      },
      maxWidth: {
        'content': '1000px',
      },
      colors: {
        text: {
          primary: '#1a1a1a',
          secondary: '#4a4a4a',
          tertiary: '#7a7a7a',
          'dark-primary': '#e5e5e5',
          'dark-secondary': '#b0b0b0',
          'dark-tertiary': '#808080',
        },
        background: '#fafaf8',
        'background-dark': '#1a1a1a',
        surface: '#ffffff',
        'surface-dark': '#2a2a2a',
        border: {
          light: '#e5e5e5',
          medium: '#d0d0d0',
          'dark-light': '#404040',
          'dark-medium': '#505050',
        },
        accent: {
          scripture: '#8b4513',
          reference: '#2c3e50',
          greek: '#1a365d',
          hebrew: '#7c2d12',
          relevance: '#d4a574',
          'dark-scripture': '#d4a574',
          'dark-reference': '#8fa9c4',
          'dark-greek': '#7faed6',
          'dark-hebrew': '#d88b6a',
          'dark-relevance': '#d4a574',
        },
        error: '#991b1b',
        'error-dark': '#f87171',
        success: '#14532d',
        'success-dark': '#86efac',
        warning: '#78350f',
        'warning-dark': '#fbbf24',
      },
    },
  },
  plugins: [],
};
