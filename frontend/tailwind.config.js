/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        // Primary Palette
        'primary-blue': {
          50: '#F0F4F8',
          100: '#E8ECF1',
          200: '#D1D9E6',
          300: '#B3C0D6',
          400: '#8FA5C1',
          500: '#6B8CAC',
          600: '#4A7396',
          700: '#2D5F8A',
          800: '#1A3A5C',
          900: '#0F2440',
        },
        // Surface Colors
        'surface': {
          white: '#FFFFFF',
          grey: '#F5F7FA',
          'grey-dark': '#E8ECF1',
        },
        // Semantic Palette
        'success': '#2E7D32',
        'warning': '#F59E0B',
        'danger': '#DC2626',
        'info': '#2563EB',
        // Text Colors
        'text': {
          primary: '#1F2937',
          secondary: '#6B7280',
          disabled: '#9CA3AF',
        }
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
