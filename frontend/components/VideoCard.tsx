export default function VideoCard({ video, label }: { video: any; label: string }) {
  if (!video) return null;

  return (
    <div className="bg-zinc-900 rounded-2xl p-6 border border-zinc-800">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-full bg-violet-600 flex items-center justify-center font-bold">
          {label}
        </div>
        <div>
          <h3 className="font-semibold">{video.title}</h3>
          <p className="text-sm text-zinc-400">{video.creator}</p>
        </div>
      </div>

      <div className="aspect-video bg-black rounded-xl mb-4 overflow-hidden">
        <iframe
          width="100%"
          height="100%"
          src={video.url.replace("watch?v=", "embed/")}
          allowFullScreen
        />
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>Views: {video.views?.toLocaleString()}</div>
        <div>Likes: {video.likes?.toLocaleString()}</div>
        <div>Engagement: <span className="text-emerald-400">{video.engagement}%</span></div>
        <div>Duration: {Math.floor(video.duration / 60)}:{(video.duration % 60).toString().padStart(2, '0')}</div>
      </div>
    </div>
  );
}