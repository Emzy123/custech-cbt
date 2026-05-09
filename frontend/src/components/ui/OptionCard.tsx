import React from 'react';
import clsx from 'clsx';

interface OptionCardProps {
  id: string;
  label: string;
  selected?: boolean;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

const OptionCard: React.FC<OptionCardProps> = ({ 
  id, 
  label, 
  selected = false, 
  disabled = false, 
  onClick, 
  children 
}) => {
  const cardClasses = clsx(
    'bg-surface-white border-2 rounded-md p-4 cursor-pointer transition-all duration-150 animate-on-hover',
    {
      'border-surface-grey-dark hover:border-info': !selected && !disabled,
      'border-info bg-blue-50': selected && !disabled,
      'border-surface-grey-dark cursor-not-allowed opacity-50': disabled,
    }
  );
  
  return (
    <div
      className={cardClasses}
      onClick={disabled ? undefined : onClick}
      role="radio"
      aria-checked={selected}
      aria-disabled={disabled}
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-1">
          <div
            className={clsx(
              'w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200',
              {
                'border-surface-grey-dark': !selected,
                'border-info bg-info': selected,
              }
            )}
          >
            {selected && (
              <div className="w-2 h-2 rounded-full bg-surface-white" />
            )}
          </div>
        </div>
        <div className="flex-1">
          <div className="font-medium text-text-primary mb-1">
            {label}
          </div>
          <div className="text-text-primary">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptionCard;
