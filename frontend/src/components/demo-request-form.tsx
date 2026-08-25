"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const DEFAULT_DEMO_REQUEST =
    "Critical production incident detected. " +
    "The database service is unavailable and " +
    "customer-facing systems are affected. " +
    "Determine the appropriate response using " +
    "the internal incident response policy.";

export default function DemoRequestForm() {
    const router = useRouter();

    const [content, setContent] =
        useState(DEFAULT_DEMO_REQUEST);

    const [isSubmitting, setIsSubmitting] =
        useState(false);

    const [message, setMessage] =
        useState<string | null>(null);

    const [error, setError] =
        useState<string | null>(null);

    async function submitDemoRequest() {
        const trimmedContent = content.trim();

        if (trimmedContent.length < 10) {
            setError(
                "Please enter at least 10 characters.",
            );
            return;
        }

        setIsSubmitting(true);
        setMessage(null);
        setError(null);

        try {
            const response = await fetch(
                "/api/demo/requests",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",
                    },
                    body: JSON.stringify({
                        content: trimmedContent,
                    }),
                },
            );

            if (!response.ok) {
                let detail =
                    `Request failed (${response.status})`;

                try {
                    const body =
                        (await response.json()) as {
                            detail?: string;
                        };

                    if (
                        typeof body.detail ===
                        "string"
                    ) {
                        detail = body.detail;
                    }
                } catch {
                    // Keep fallback message.
                }

                throw new Error(detail);
            }

            setMessage(
                "Demo request submitted. " +
                "The AI workflow is now processing it.",
            );

            router.refresh();
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Demo request failed",
            );
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <section className="panel demo-panel">
            <div className="panel-heading">
                <div>
                    <p className="eyebrow">
                        Interactive Public Demo
                    </p>

                    <h2>
                        Try the Live AI Workflow
                    </h2>
                </div>

                <span className="count">
                    Demo Safe
                </span>
            </div>

            <p className="demo-description">
                Submit a simulated business incident
                and follow the workflow through AI
                analysis, RAG policy retrieval,
                Human-in-the-Loop approval and the
                audit trail.
            </p>

            <div className="demo-form">
                <label htmlFor="demo-request">
                    Business incident
                </label>

                <textarea
                    id="demo-request"
                    value={content}
                    maxLength={1000}
                    rows={6}
                    onChange={(event) =>
                        setContent(
                            event.target.value,
                        )
                    }
                    disabled={isSubmitting}
                />

                <div className="demo-form-footer">
                    <small>
                        {content.length}/1000
                    </small>

                    <button
                        type="button"
                        className="button button-approve"
                        disabled={
                            isSubmitting ||
                            content.trim().length < 10
                        }
                        onClick={
                            submitDemoRequest
                        }
                    >
                        {isSubmitting
                            ? "Starting Workflow..."
                            : "Run AI Workflow"}
                    </button>
                </div>

                {message && (
                    <p className="demo-success">
                        {message}
                    </p>
                )}

                {error && (
                    <p className="action-error">
                        {error}
                    </p>
                )}
            </div>
        </section>
    );
}