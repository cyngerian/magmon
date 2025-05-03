import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChangePasswordModal from '../ChangePasswordModal';
import apiClient from '../../apiClient';

// Mock the apiClient
vi.mock('../../apiClient', () => ({
  default: {
    post: vi.fn(),
  },
}));

describe('ChangePasswordModal', () => {
  const mockOnSuccess = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    // Mock console.error to avoid polluting test output with expected errors
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore console.error
    vi.restoreAllMocks();
  });

  const renderComponent = (props = {}) => {
    const defaultProps = {
      onSuccess: mockOnSuccess,
      onClose: mockOnClose,
    };
    return render(<ChangePasswordModal {...defaultProps} {...props} />);
  };

  it('renders the modal with required fields', () => {
    renderComponent();
    expect(screen.getByRole('heading', { name: /Change Password Required/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Current Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/New Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm New Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Change Password/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
  });

  it('does not render cancel button if onClose is not provided', () => {
    renderComponent({ onClose: undefined });
    expect(screen.queryByRole('button', { name: /Cancel/i })).not.toBeInTheDocument();
  });

  it('shows an error if new passwords do not match', async () => {
    const user = userEvent.setup();
    renderComponent();

    await user.type(screen.getByLabelText(/Current Password/i), 'oldPassword123');
    await user.type(screen.getByLabelText(/New Password/i), 'newPassword123');
    await user.type(screen.getByLabelText(/Confirm New Password/i), 'differentPassword');
    await user.click(screen.getByRole('button', { name: /Change Password/i }));

    expect(screen.getByText(/New passwords do not match/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it('shows an error if new password is less than 8 characters', async () => {
    const user = userEvent.setup();
    renderComponent();

    await user.type(screen.getByLabelText(/Current Password/i), 'oldPassword123');
    await user.type(screen.getByLabelText(/New Password/i), 'short');
    await user.type(screen.getByLabelText(/Confirm New Password/i), 'short');
    await user.click(screen.getByRole('button', { name: /Change Password/i }));

    expect(screen.getByText(/New password must be at least 8 characters long/i)).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it('calls API and onSuccess on successful password change', async () => {
    const user = userEvent.setup();
    const mockResponse = {
      data: {
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token',
      },
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    renderComponent();

    await user.type(screen.getByLabelText(/Current Password/i), 'oldPassword123');
    await user.type(screen.getByLabelText(/New Password/i), 'newValidPassword123');
    await user.type(screen.getByLabelText(/Confirm New Password/i), 'newValidPassword123');
    await user.click(screen.getByRole('button', { name: /Change Password/i }));

    expect(apiClient.post).toHaveBeenCalledTimes(1);
    expect(apiClient.post).toHaveBeenCalledWith('/change-password', {
      current_password: 'oldPassword123',
      new_password: 'newValidPassword123',
    });

    // Check loading state during API call
    expect(screen.getByRole('button', { name: /Change Password/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Change Password/i })).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeDisabled();

    // Wait for the promise to resolve
    await vi.waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalledTimes(1);
      expect(mockOnSuccess).toHaveBeenCalledWith({
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token',
      });
    });

     // Check buttons are enabled again after call finishes
    expect(screen.getByRole('button', { name: /Change Password/i })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Change Password/i })).toHaveAttribute('aria-busy', 'false');
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeEnabled();
    expect(screen.queryByText(/Failed to change password/i)).not.toBeInTheDocument(); // No error shown
  });

  it('shows an error message if API call fails', async () => {
    const user = userEvent.setup();
    const mockError = {
      response: {
        data: { error: 'Invalid current password' },
      },
    };
    (apiClient.post as ReturnType<typeof vi.fn>).mockRejectedValue(mockError);

    renderComponent();

    await user.type(screen.getByLabelText(/Current Password/i), 'wrongOldPassword');
    await user.type(screen.getByLabelText(/New Password/i), 'newValidPassword123');
    await user.type(screen.getByLabelText(/Confirm New Password/i), 'newValidPassword123');
    await user.click(screen.getByRole('button', { name: /Change Password/i }));

    expect(apiClient.post).toHaveBeenCalledTimes(1);

    // Wait for the promise to resolve and error to show
    await vi.waitFor(() => {
      expect(screen.getByText(/Invalid current password/i)).toBeInTheDocument();
    });

    expect(mockOnSuccess).not.toHaveBeenCalled();
    // Check buttons are enabled again after call finishes
    expect(screen.getByRole('button', { name: /Change Password/i })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeEnabled();
  });

   it('shows a generic error message if API call fails without specific error data', async () => {
    const user = userEvent.setup();
    const mockError = new Error('Network Error'); // Generic error
    (apiClient.post as ReturnType<typeof vi.fn>).mockRejectedValue(mockError);

    renderComponent();

    await user.type(screen.getByLabelText(/Current Password/i), 'oldPassword123');
    await user.type(screen.getByLabelText(/New Password/i), 'newValidPassword123');
    await user.type(screen.getByLabelText(/Confirm New Password/i), 'newValidPassword123');
    await user.click(screen.getByRole('button', { name: /Change Password/i }));

    expect(apiClient.post).toHaveBeenCalledTimes(1);

    // Wait for the promise to resolve and error to show
    await vi.waitFor(() => {
      expect(screen.getByText(/Failed to change password/i)).toBeInTheDocument();
    });

    expect(mockOnSuccess).not.toHaveBeenCalled();
  });

  it('calls onClose when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    renderComponent();

    await user.click(screen.getByRole('button', { name: /Cancel/i }));

    expect(mockOnClose).toHaveBeenCalledTimes(1);
    expect(apiClient.post).not.toHaveBeenCalled();
    expect(mockOnSuccess).not.toHaveBeenCalled();
  });
});