import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '../test-utils';
import Navbar from './Navbar';

describe('Navbar supplier access', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('lets Approvers reach the Suppliers page', () => {
    render(
      <Navbar />,
      {
        user: { email: 'approver@test.com', fullName: 'Approver User', roles: ['Approver'] },
        token: 'fake-jwt-token',
        route: '/dashboard',
      },
    );

    expect(screen.getByRole('link', { name: 'Suppliers' })).toHaveAttribute('href', '/suppliers');
  });
});
