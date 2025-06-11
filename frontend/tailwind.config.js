/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand Colors from your design system
        primary: {
          DEFAULT: '#103E60',    // Main primary color
          50: '#f0f7ff',
          100: '#e0efff',
          200: '#b9ddff',
          300: '#7cc4ff',
          400: '#36a7ff',
          500: '#0d8bff',
          600: '#103E60',        // Your primary
          700: '#0f3554',
          800: '#132d45',
          900: '#15263b',
        },
        secondary: {
          DEFAULT: '#54595F',    // Your secondary
          50: '#f6f7f8',
          100: '#eaecee',
          200: '#d9dcdf',
          300: '#bdc2c8',
          400: '#9ca3ab',
          500: '#808891',
          600: '#6c727a',
          700: '#54595F',        // Your secondary
          800: '#4a4e53',
          900: '#414549',
        },
        accent: {
          DEFAULT: '#61CE70',    // Your accent green
          50: '#f0fdf1',
          100: '#dcfce1',
          200: '#bbf7c5',
          300: '#86ef9c',
          400: '#61CE70',        // Your accent
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        success: '#23A455',      // Your success green
        warning: '#FF9419',      // Your warning orange
        danger: '#FF4939',       // Your error red
        info: '#3957FF',         // Your info blue
        
        // Text Colors
        text: {
          primary: '#515151',    // Your main text
          secondary: '#6C6C6C',  // Your secondary text
          light: '#BABABA',      // Your light text
          dark: '#051B34',       // Your dark text
        },
        
        // Background Colors
        bg: {
          primary: '#FFFFFF',    // White background
          secondary: '#EFEFEF',  // Light gray background
          accent: '#DBDBDB',     // Accent background
          dark: '#051B34',       // Dark background
        },
        
        // UI Colors
        border: '#DBDBDB',       // Border color
        muted: '#EFEFEF',        // Muted elements
      },
      fontFamily: {
        sans: ['Open Sans', 'system-ui', 'sans-serif'],
        primary: ['Open Sans', 'system-ui', 'sans-serif'],
      },
      fontWeight: {
        'primary': '600',
        'secondary': '400', 
        'accent': '500',
      },
      fontSize: {
        'base': ['15px', '1.5em'],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      }
    },
  },
  plugins: [],
} 