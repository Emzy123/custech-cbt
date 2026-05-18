import React from 'react';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || `input-${React.useId()}`;
    
    const inputClasses = clsx(
      'w-full h-12 bg-white border-2 rounded-md transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-custech-navy focus:ring-opacity-15 text-text-dark placeholder-text-placeholder',
      {
        'border-input': !error,
        'border-danger': error,
      },
      className
    );
    
    return (
      <div className="space-y-2">
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-body text-sm font-medium transition-colors duration-150 peer-focus:text-custech-navy"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={inputClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-danger text-sm" role="alert">
            {error}
          </p>
        )}
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="text-muted text-sm">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
