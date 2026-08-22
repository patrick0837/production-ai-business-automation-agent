"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import type { AgentAction } from "@/lib/api";

type Props = {
    action: AgentAction;
};

function getStringArgument(
    action: AgentAction,
    key: string,
) {
    const value = action.arguments?.[key];

    return typeof value === "string"
        ? value
        : null;
}

export default function ApprovalCard({
                                         action,
                                     }: Props) {
    const router = useRouter();

    const [isRejecting, setIsRejecting] =
        useState(false);

    const [rejectionReason, setRejectionReason] =
        useState("");

    const [isSubmitting, setIsSubmitting] =
        useState(false);

    const [error, setError] =
        useState<string | null>(null);

    const reason = getStringArgument(
        action,
        "reason",
    );

    const severity = getStringArgument(
        action,
        "severity",
    );

    async function approveAction() {
        setIsSubmitting(true);
        setError(null);

        try {
            const response = await fetch(
                `/api/agent-actions/${action.id}/approve`,
                {
                    method: "POST",
                },
            );

            if (!response.ok) {
                throw new Error(
                    `Approval failed (${response.status})`,
                );
            }

            router.refresh();
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Approval failed",
            );
        } finally {
            setIsSubmitting(false);
        }
    }

    async function rejectAction() {
        const reasonValue =
            rejectionReason.trim();

        if (!reasonValue) {
            setError(
                "Please provide a rejection reason.",
            );
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            const response = await fetch(
                `/api/agent-actions/${action.id}/reject`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        reason: reasonValue,
                    }),
                },
            );

            if (!response.ok) {
                throw new Error(
                    `Rejection failed (${response.status})`,
                );
            }

            setIsRejecting(false);
            setRejectionReason("");

            router.refresh();
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Rejection failed",
            );
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="approval-card">
            <div className="approval-header">
                <div>
                    <strong className="approval-tool">
                        {action.tool_name}
                    </strong>

                    <p>
                        Request{" "}
                        {action.business_request_id.slice(
                            0,
                            8,
                        )}
                    </p>
                </div>

                <span className="badge badge-pending-approval">
          Pending Approval
        </span>
            </div>

            {(severity || reason) && (
                <div className="approval-details">
                    {severity && (
                        <div>
                            <span>Severity</span>
                            <strong>{severity}</strong>
                        </div>
                    )}

                    {reason && (
                        <div>
                            <span>Reason</span>
                            <strong>{reason}</strong>
                        </div>
                    )}
                </div>
            )}

            {isRejecting && (
                <div className="rejection-box">
                    <label
                        htmlFor={`reason-${action.id}`}
                    >
                        Rejection reason
                    </label>

                    <textarea
                        id={`reason-${action.id}`}
                        value={rejectionReason}
                        onChange={(event) =>
                            setRejectionReason(
                                event.target.value,
                            )
                        }
                        placeholder="Explain why this action should not execute..."
                        rows={3}
                    />
                </div>
            )}

            {error && (
                <p className="action-error">
                    {error}
                </p>
            )}

            <div className="approval-actions">
                <button
                    className="button button-approve"
                    type="button"
                    disabled={isSubmitting}
                    onClick={approveAction}
                >
                    {isSubmitting
                        ? "Processing..."
                        : "Approve"}
                </button>

                {!isRejecting ? (
                    <button
                        className="button button-reject"
                        type="button"
                        disabled={isSubmitting}
                        onClick={() =>
                            setIsRejecting(true)
                        }
                    >
                        Reject
                    </button>
                ) : (
                    <>
                        <button
                            className="button button-reject"
                            type="button"
                            disabled={isSubmitting}
                            onClick={rejectAction}
                        >
                            Confirm Reject
                        </button>

                        <button
                            className="button button-secondary"
                            type="button"
                            disabled={isSubmitting}
                            onClick={() => {
                                setIsRejecting(false);
                                setRejectionReason("");
                                setError(null);
                            }}
                        >
                            Cancel
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}