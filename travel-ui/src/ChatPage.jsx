import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {

	const WELCOME = {
		role: "assistant",
		content: `**Welcome to Trip Planner!**

I can help you plan your next trip. Here's how to get started:

- **Tell me your travel plans:** Where you want to go, your travel dates or trip length, and your budget.
- **Find flights and hotels:** I can search flight schedules and recommend hotels. Flight ticket prices are not available.
- **Customize your trip:** Ask me to change your itinerary, find cheaper hotels, or suggest other activities.
- **Continue the conversation:** I remember the details during this chat, but refreshing the page or clicking the New trip button starts a new conversation.

_Example: "Plan a 3-day trip to Tokyo from Kuala Lumpur with a mid-range budget."_`,
	};

	const [messages, setMessages] = useState([WELCOME]);
	const [threadId, setThreadId] = useState(() => crypto.randomUUID());
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);
	const bottomRef = useRef(null);

	const API_URL = "http://127.0.0.1:8000";

	function newTrip() {
		setMessages([WELCOME]);
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
					{messages.length > 1 && (
						<button
							onClick={newTrip}
							className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:border-sky-600"
						>
							New trip
						</button>
					)}
				</header>

				<main className="flex flex-1 flex-col gap-3 overflow-y-auto p-5">
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
