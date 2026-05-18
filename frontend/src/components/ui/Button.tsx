import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'light';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading = false, disabled, children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed';
    
    const variantClasses = {
      primary: 'bg-custech-primary text-white hover:bg-custech-primary hover:shadow-lg hover:scale-105 focus:ring-custech-navy disabled:bg-border-default disabled:text-text-muted',
      secondary: 'bg-transparent text-custech-primary border-2 border-custech-primary hover:bg-custech-primary hover:text-white focus:ring-custech-navy disabled:border-default disabled:text-text-muted',
      outline: 'bg-transparent text-custech-primary border-2 border-custech-primary hover:bg-custech-primary hover:text-white focus:ring-custech-navy disabled:border-default disabled:text-text-muted',
      light: 'bg-white text-custech-primary hover:bg-gray-50 focus:ring-custech-navy disabled:bg-light disabled:text-text-muted',
    };
    
    const sizeClasses = {
      sm: 'px-4 py-2 text-sm',
      md: 'px-6 py-3 text-base',
      lg: 'px-8 py-4 text-lg',
    };
    
    const classes = clsx(
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      className
    );
    
    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
