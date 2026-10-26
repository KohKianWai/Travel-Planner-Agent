import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
	const [messages, setMessages] = useState([]);
	const [threadId, setThreadId] = useState(() => crypto.randomUUID());
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);
	const bottomRef = useRef(null);

	const API_URL = "http://127.0.0.1:8000";

	function newTrip() {
		setMessages([]);
		setThreadId(crypto.randomUUID());
	}

	function onKeyDown(e) {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			send(input);
		}
	}

	useEffect(() => {
		bottomRef.current?.scrollIntoView({
			behavior: "smooth",
			block: "end"
		});
	}, [messages]);

	async function send(text) {
		const message = text.trim();
		if (!message || loading) return;

		setMessages((m) => [...m, { role: "user", content: message }]);
		setInput("");
		setLoading(true);
		console.log(`Thread_id: ${threadId}`)
		try {
			const res = await fetch(`${API_URL}/api/travel`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ message, thread_id: threadId })
			});

			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				throw new Error(err.detail || `Request failed (${res.status})`);
			}

			const data = await res.json();
			setMessages((m) => [...m, { role: "assistant", content: data.answer }]);
		} catch (e) {
			setMessages((m) => [
				...m,
				{
					role: "error",
					content: `${e.message}. Check your connection and try again.`
				}
			]);
		} finally {
			setLoading(false);
		}
	}

	const EXAMPLES = [
		"5 days in Tokyo from Kuala Lumpur, mid-range budget",
		"Weekend in Bangkok, I love street food",
		"Hotels near Shibuya for 3 nights"
	];

	const bubble = {
		user: "self-end rounded-br-sm bg-sky-700 text-white whitespace-pre-wrap",
		assistant: "self-start rounded-bl-sm border border-slate-300 bg-white",
		error: "self-start border border-red-700 text-red-700"
	};

	return (
		<div className="h-screen bg-slate-200 p-4 md:p-8">
			<div className="mx-auto flex h-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-slate-100 text-slate-900 shadow-lg">
				<header className="flex items-center justify-between border-b-2 border-dashed border-slate-300 px-5 py-4">
					<div>
						<h1 className="text-2xl font-bold">Trip planner</h1>
						<p className="text-sm text-slate-600">
							Flights, hotels and a day-by-day plan
						</p>
					</div>
					{messages.length > 0 && (
						<button
							onClick={newTrip}
							className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:border-sky-600"
						>
							New trip
						</button>
					)}
				</header>

				<main className="flex flex-1 flex-col gap-3 overflow-y-auto p-5">
					{messages.length === 0 && (
						<div className="my-auto">
							<p className="mb-3 text-slate-600">
								Tell me where you want to go, for how long, and your budget.
							</p>
							<div className="flex flex-col items-start gap-2">
								{EXAMPLES.map((ex) => (
									<button
										key={ex}
										onClick={() => send(ex)}
										className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-left hover:border-sky-600"
									>
										{ex}
									</button>
								))}
							</div>
						</div>
					)}

					{messages.map((m, i) => (
						<div
							key={i}
							className={`max-w-[88%] rounded-xl px-4 py-3 ${bubble[m.role]}`}
						>
							{m.role === "assistant" ? (
								<div className="prose prose-sm max-w-none">
									<ReactMarkdown>{m.content}</ReactMarkdown>
								</div>
							) : (
								<p>{m.content}</p>
							)}
						</div>
					))}

					{loading && (
						<div className={`flex gap-1.5 rounded-xl p-4 ${bubble.assistant}`}>
							{[0, 150, 300].map((delay) => (
								<span
									key={delay}
									style={{ animationDelay: `${delay}ms` }}
									className="h-2 w-2 animate-pulse rounded-full bg-slate-500"
								/>
							))}
						</div>
					)}
					<div ref={bottomRef} />
				</main>

				<form
					onSubmit={(e) => {
						e.preventDefault();
						send(input);
					}}
					className="flex gap-2 border-t border-slate-300 p-4"
				>
					<textarea
						rows={1}
						value={input}
						onChange={(e) => setInput(e.target.value)}
						onKeyDown={onKeyDown}
						placeholder="Where to next?"
						className="flex-1 resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 h-16"
					/>
					<button
						type="submit"
						disabled={loading || !input.trim()}
						className="rounded-lg bg-sky-700 cursor-pointer px-5 font-semibold text-white hover:bg-sky-800 disabled:opacity-50"
					>
						Send
					</button>
				</form>
			</div>
		</div>
	);
}
