/** @type {import('tailwindcss').Config} */
export const darkMode = 'class';
export const content = [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}"
];
export const theme = {
    extend: {
        colors: {
            // Optional: Custom royal blue for accents
            'space-blue': {
                DEFAULT: '#223366',
                dark: '#162447',
                accent: '#3a7ca5',
            },
        },
    },
};
export const plugins = [];
  