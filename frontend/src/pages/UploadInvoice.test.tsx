import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../test-utils';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import UploadInvoice from './UploadInvoice';
import { uploadInvoiceHandlers } from './UploadInvoice.handlers';

describe('UploadInvoice', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Task 1.2 — Happy path: successful upload shows extraction form', () => {
    it('shows extraction review form after selecting a PDF and clicking upload', async () => {
      server.use(...uploadInvoiceHandlers);

      render(<UploadInvoice />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/upload',
      });

      // Wait for auth to load and the upload form to render
      const fileInput = await screen.findByTestId('file-input');

      // Select a valid PDF file
      const file = new File(['dummy pdf content'], 'invoice.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      // Click Upload & Analyze
      const uploadButton = screen.getByTestId('upload-button');
      fireEvent.click(uploadButton);

      // Verify processing state is shown during upload
      expect(screen.getByText('Processing AI Extraction...')).toBeInTheDocument();

      // Wait for extraction form to appear
      await waitFor(() => {
        expect(screen.getByText('Review Extracted Data')).toBeInTheDocument();
      });

      // Verify extracted data is rendered in the form
      expect(screen.getByDisplayValue('Acme Corp')).toBeInTheDocument();
      expect(screen.getByDisplayValue('INV-2024-001')).toBeInTheDocument();
      expect(screen.getByDisplayValue('2024-01-15')).toBeInTheDocument();
    });
  });

  describe('Task 1.3 — API Error 500: user-friendly notification', () => {
    it('shows inline error message when server responds with 500 and preserves upload form', async () => {
      server.use(
        http.post('http://localhost:8000/api/invoices/upload', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      render(<UploadInvoice />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/upload',
      });

      // Wait for auth to load and the upload form to render
      const fileInput = await screen.findByTestId('file-input');

      // Select valid PDF
      const file = new File(['dummy pdf content'], 'invoice.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      // Click upload
      fireEvent.click(screen.getByTestId('upload-button'));

      // Wait for inline error to appear
      await waitFor(() => {
        expect(screen.getByTestId('server-error')).toHaveTextContent('Error uploading invoice. Please try again.');
      });

      // Upload form is preserved for retry
      expect(screen.getByTestId('file-input')).toBeInTheDocument();
      expect(screen.getByTestId('upload-button')).toBeInTheDocument();
    });
  });

  describe('Task 1.6 — Duplicate invoice number returns 409 and shows specific error', () => {
    it('shows duplicate invoice error when server responds with 409', async () => {
      server.use(
        http.post('http://localhost:8000/api/invoices/upload', () => {
          return HttpResponse.json(
            { detail: "Duplicate invoice: invoice number 'INV-2024-001' already exists for supplier 'Acme Corp'." },
            { status: 409 }
          );
        })
      );

      render(<UploadInvoice />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/upload',
      });

      const fileInput = await screen.findByTestId('file-input');
      const file = new File(['dummy pdf content'], 'invoice.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      fireEvent.click(screen.getByTestId('upload-button'));

      await waitFor(() => {
        expect(screen.getByTestId('server-error')).toHaveTextContent(
          "Duplicate invoice: invoice number 'INV-2024-001' already exists for supplier 'Acme Corp'."
        );
      });

      // Upload form is preserved for retry
      expect(screen.getByTestId('file-input')).toBeInTheDocument();
      expect(screen.getByTestId('upload-button')).toBeInTheDocument();
    });
  });

  describe('Task 1.4 — Local validation: non-PDF file rejected', () => {
    it('displays validation error for non-PDF file and does not call the API', async () => {
      // No handler needed — API should never be called

      render(<UploadInvoice />, {
        user: { email: 'admin@test.com', fullName: 'Admin User', roles: ['Admin'] },
        token: 'fake-jwt-token',
        route: '/upload',
      });

      // Wait for auth to load and the upload form to render
      const fileInput = await screen.findByTestId('file-input');

      // Select a .txt file (non-PDF)
      const file = new File(['text content'], 'readme.txt', { type: 'text/plain' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      // Click upload
      fireEvent.click(screen.getByTestId('upload-button'));

      // Validation error should be displayed
      await waitFor(() => {
        expect(screen.getByTestId('validation-error')).toHaveTextContent('Only PDF files are accepted');
      });

      // Alert should NOT have been called (API never reached)
      expect(window.alert).not.toHaveBeenCalled();
    });
  });

  describe('Task 1.5 — Role access: Viewer role restriction', () => {
    it('shows restricted message and does not render upload form for Viewer role', async () => {
      render(<UploadInvoice />, {
        user: { email: 'viewer@test.com', fullName: 'Viewer User', roles: ['Viewer'] },
        token: 'fake-jwt-token',
        route: '/upload',
      });

      // Wait for auth to load, then check restricted message
      await waitFor(() => {
        expect(screen.getByTestId('restricted-message')).toHaveTextContent(
          'You do not have permission to upload invoices'
        );
      });

      // Upload button should NOT be present
      expect(screen.queryByTestId('upload-button')).not.toBeInTheDocument();
    });
  });
});
