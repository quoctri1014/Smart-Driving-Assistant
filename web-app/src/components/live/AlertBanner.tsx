export default function AlertBanner({ message, level }: { message: string | null; level: "normal" | "warning" | "critical" }) {
    if (!message || level === "normal") return null;

    const bgColors = {
        warning: "bg-yellow-500",
        critical: "bg-red-600"
    };

    return (
        <div className={`absolute top-10 inset-x-4 p-4 rounded-xl shadow-lg text-white font-bold text-center z-50 animate-bounce ${bgColors[level]}`}>
            ⚠️ {message}
        </div>
    );
}
