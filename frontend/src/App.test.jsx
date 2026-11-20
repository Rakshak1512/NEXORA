import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import Button from './components/common/Button';
import Badge from './components/common/Badge';
import HealthIndicator from './components/common/HealthIndicator';

describe('Common UI Components', () => {
  it('renders Button correctly', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('renders Badge with correct label', () => {
    render(<Badge variant="success">ACTIVE</Badge>);
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('renders 4 Mandatory Health States', () => {
    const { rerender } = render(<HealthIndicator state="EXCELLENT" />);
    expect(screen.getByText('EXCELLENT')).toBeInTheDocument();

    rerender(<HealthIndicator state="GOOD" />);
    expect(screen.getByText('GOOD')).toBeInTheDocument();

    rerender(<HealthIndicator state="FAIR" />);
    expect(screen.getByText('FAIR')).toBeInTheDocument();

    rerender(<HealthIndicator state="POOR" />);
    expect(screen.getByText('POOR')).toBeInTheDocument();
  });
});

