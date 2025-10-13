import { Card } from "antd";
import { Star } from "lucide-react";

export default function Reviews({ operator }) {
  return (
    <div className="flex flex-col gap-4">
      {/* 评分统计 */}
      <Card>
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">4.7</div>
            <div className="flex items-center justify-center gap-1 mt-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className="w-4 h-4 fill-yellow-400 text-yellow-400"
                />
              ))}
            </div>
            <div className="text-sm text-gray-600 mt-1">
              基于 {operator.reviews.length} 个评价
            </div>
          </div>
          <div className="flex-1">
            <div className="space-y-2">
              {[5, 4, 3, 2, 1].map((rating) => {
                const count = operator.reviews.filter(
                  (r) => r.rating === rating
                ).length;
                const percentage = (count / operator.reviews.length) * 100;
                return (
                  <div key={rating} className="flex items-center gap-2">
                    <span className="text-sm text-gray-600 w-8">
                      {rating}星
                    </span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-yellow-400 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-8">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Card>

      {/* 评价列表 */}
      {operator.reviews.map((review) => (
        <Card key={review.id}>
          <div className="flex items-start gap-4">
            <img
              src={review.avatar || "/placeholder.svg"}
              alt={review.user}
              className="w-10 h-10 rounded-full"
            />
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h4 className="font-medium text-gray-900">{review.user}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`w-4 h-4 ${
                            star <= review.rating
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-gray-300"
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-sm text-gray-600">{review.date}</span>
                  </div>
                </div>
              </div>
              <p className="text-gray-700">{review.comment}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
