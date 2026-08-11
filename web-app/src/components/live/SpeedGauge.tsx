export default function SpeedGauge({ current, recommended }: { current: number; recommended: number }) {
    const isSpeeding = current > recommended;
    
    return (
        <div className="absolute bottom-6 inset-x-4 bg-white/90 backdrop-blur-sm p-4 rounded-2xl shadow-xl flex items-center justify-between z-40">
            <div>
                <p className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Current Speed</p>
                <p className={`text-4xl font-black ${isSpeeding ? 'text-red-500' : 'text-slate-800'}`}>
                    {current} <span className="text-lg text-gray-500">km/h</span>
                </p>
            </div>
            
            <div className="text-right">
                <p className="text-gray-500 text-xs font-semibold uppercase tracking-wider">Recommended</p>
                <div className="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xl font-bold mt-1">
                    {recommended}
                </div>
            </div>
        </div>
    );
}
