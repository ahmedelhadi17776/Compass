/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx}"
  ],
  darkMode: ['class', "class"],
  theme: {
    extend: {
      fontFamily: {
        poppins: ['Poppins', 'sans-serif'],
        custom: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        apple: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))'
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))'
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))'
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))'
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))'
        },
        chart: {
          '1': 'hsl(var(--chart-1))',
          '2': 'hsl(var(--chart-2))',
          '3': 'hsl(var(--chart-3))',
          '4': 'hsl(var(--chart-4))',
          '5': 'hsl(var(--chart-5))'
        },
        typography: {
          DEFAULT: {
            css: {
              color: 'hsl(var(--foreground))',
              a: {
                color: 'hsl(var(--primary))',
                '&:hover': {
                  color: 'hsl(var(--primary))',
                },
              },
              strong: {
                color: 'hsl(var(--foreground))',
              },
              'ol > li::marker': {
                color: 'hsl(var(--foreground))',
              },
              'ul > li::marker': {
                color: 'hsl(var(--foreground))',
              },
              hr: {
                borderColor: 'hsl(var(--border))',
              },
              blockquote: {
                borderLeftColor: 'hsl(var(--border))',
                color: 'hsl(var(--foreground))',
              },
              h1: {
                color: 'hsl(var(--foreground))',
              },
              h2: {
                color: 'hsl(var(--foreground))',
              },
              h3: {
                color: 'hsl(var(--foreground))',
              },
              h4: {
                color: 'hsl(var(--foreground))',
              },
              'figure figcaption': {
                color: 'hsl(var(--muted-foreground))',
              },
              code: {
                color: 'hsl(var(--foreground))',
              },
              'a code': {
                color: 'hsl(var(--primary))',
              },
              pre: {
                color: 'hsl(var(--foreground))',
                backgroundColor: 'hsl(var(--muted))',
              },
              thead: {
                color: 'hsl(var(--foreground))',
                borderBottomColor: 'hsl(var(--border))',
              },
              'tbody tr': {
                borderBottomColor: 'hsl(var(--border))',
              },
            },
          },
        },
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          primary: 'hsl(var(--sidebar-primary))',
          'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
          border: 'hsl(var(--sidebar-border))',
          ring: 'hsl(var(--sidebar-ring))'
        }
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require("tailwindcss-animate"),
    require('@tailwindcss/typography'),
  ],
}