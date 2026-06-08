import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eeedfe',
          100: '#cecbf6',
          500: '#534ab7',
          600: '#3c3489',
          900: '#26215c',
        },
      },
    },
  },
  plugins: [],
} satisfies Config
