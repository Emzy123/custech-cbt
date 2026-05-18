import React from 'react';
import clsx from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevation?: 0 | 1 | 2 | 3;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  variant?: 'default' | 'announcement' | 'featured';
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, elevation = 1, padding = 'md', variant = 'default', children, ...props }, ref) => {
    const elevationClasses = {
      0: 'shadow-elevation-0',
      1: 'shadow-elevation-1',
      2: 'shadow-elevation-2',
      3: 'shadow-elevation-3',
    };
    
    const variantClasses = {
      default: 'bg-white rounded-md',
      announcement: 'bg-glass-bg backdrop-blur-md rounded-md border border-card hover:bg-glass-bg-hover transition-all duration-300 relative overflow-hidden',
      featured: 'bg-gradient-primary text-white rounded-md relative overflow-hidden',
    };
    
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };
    
    const classes = clsx(
      variantClasses[variant],
      elevationClasses[elevation],
      paddingClasses[padding],
      className
    );
    
    return (
      <div ref={ref} className={classes} {...props}>
        {variant === 'announcement' && (
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-gold" />
        )}
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card;
