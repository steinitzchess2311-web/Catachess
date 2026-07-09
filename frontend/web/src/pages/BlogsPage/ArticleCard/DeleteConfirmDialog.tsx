/**
 * Created at: 2026-07-09 01:34 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:34 EDT
 * Last Modified by: Codex
 *
 * DeleteConfirmDialog - confirmation dialog for article delete actions.
 */

import React from "react";
import { Cross2Icon, CheckIcon } from "@radix-ui/react-icons";

interface DeleteConfirmDialogProps {
  show: boolean;
  dialogRef: React.RefObject<HTMLDivElement>;
  onConfirm: () => void;
  onCancel: () => void;
}

const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
  show,
  dialogRef,
  onConfirm,
  onCancel,
}) => {
  if (!show) return null;

  return (
    <div
      ref={dialogRef}
      className="blog-delete-popover"
    >
      <p className="blog-delete-popover__title">
        Delete this article?
      </p>
      <div className="blog-delete-popover__actions">
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onCancel();
          }}
          className="blog-delete-popover__button"
          aria-label="Cancel delete"
        >
          <Cross2Icon width={18} height={18} />
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onConfirm();
          }}
          className="blog-delete-popover__button is-danger"
          aria-label="Confirm delete"
        >
          <CheckIcon width={18} height={18} />
        </button>
      </div>
    </div>
  );
};

export default DeleteConfirmDialog;
