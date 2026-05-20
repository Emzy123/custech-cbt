/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        // Flat aliases (used across dashboards; nested keys are text-*, bg-bg-*, etc.)
        dark: '#181818',
        darker: '#202020',
        muted: '#747474',
        light: '#F4F4F4',
        heading: '#161616',
        body: '#6B6B6B',
        placeholder: '#5E5E5E',
        // CUStech Brand Colors
        'custech': {
          primary: '#591F00',
          'primary-light': '#7A2C0D',
          'primary-dark': '#4A1900',
          gold: '#FFD54F',
          'gold-light': '#FFECB3',
          green: '#3DB166',
          'navy': '#163269',
        },
        // Gradients
        'gradient-primary': 'linear-gradient(135deg, #591F00 0%, #7A2C0D 50%, #4A1900 100%)',
        'gradient-gold': 'linear-gradient(to bottom, #FFD54F, #FFECB3)',
        // Text Colors
        'text': {
          heading: '#161616',
          body: '#6B6B6B',
          muted: '#747474',
          dark: '#4E4E4E',
          placeholder: '#5E5E5E',
        },
        // Link Colors
        'link': {
          default: '#545454',
          hover: '#591F00',
        },
        // Background Colors
        'bg': {
          white: '#FFFFFF',
          light: '#F4F4F4',
          dark: '#181818',
          darker: '#202020',
        },
        // Border Colors
        'border': {
          default: '#E6E6E6',
          light: '#D7D7D7',
          input: '#D7D7D7',
          nav: '#E8E8E8',
          card: 'rgba(255, 255, 255, 0.15)',
        },
        // Glassmorphism
        'glass': {
          bg: 'rgba(255, 255, 255, 0.08)',
          'bg-hover': 'rgba(255, 255, 255, 0.15)',
        },
        // Semantic Palette (Updated)
        'success': '#3DB166',
        'warning': '#FFD54F',
        'danger': '#DC2626',
        'info': '#163269',
        // Legacy Surface Colors (Mapped)
        'surface': {
          white: '#FFFFFF',
          grey: '#F4F4F4',
          'grey-dark': '#E6E6E6',
        },
      },
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
        'lora': ['Lora', 'serif'],
      },
      fontSize: {
        'xs': ['12px', { lineHeight: '18px' }],
        'sm': ['14px', { lineHeight: '21px' }],
        'base': ['16px', { lineHeight: '25.6px' }],
        'lg': ['20px', { lineHeight: '30px' }],
        'xl': ['25px', { lineHeight: '35px' }],
        '2xl': ['31px', { lineHeight: '40px' }],
        '3xl': ['39px', { lineHeight: '47px' }],
      },
      spacing: {
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
      },
      boxShadow: {
        'elevation-0': 'none',
        'elevation-1': '0 1px 3px rgba(0,0,0,0.08)',
        'elevation-2': '0 4px 12px rgba(0,0,0,0.10)',
        'elevation-3': '0 8px 24px rgba(0,0,0,0.14)',
      },
      borderColor: {
        DEFAULT: '#E6E6E6',
        default: '#E6E6E6',
        light: '#D7D7D7',
        input: '#D7D7D7',
        nav: '#E8E8E8',
      },
      borderRadius: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'full': '9999px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scale-subtle': 'scale-subtle 150ms ease-out',
        'fade-in': 'fade-in 300ms ease-out',
        'slide-up': 'slide-up 250ms cubic-bezier(0.4, 0, 0.2, 1)',
      },
      keyframes: {
        'scale-subtle': {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
          '100%': { transform: 'scale(1)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { 
            opacity: '0',
            transform: 'translateY(20px)'
          },
          '100%': { 
            opacity: '1',
            transform: 'translateY(0)'
          },
        },
      },
      screens: {
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },
    },
  },
  plugins: [],
}
