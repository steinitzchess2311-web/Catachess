import React from "react";
import { Link } from "react-router-dom";
type PlayerCardProps = {
  id: string;
  name: string;
  aliases?: string[];
  analyzed: number;
  updatedAt: string;
};

const PlayerCard: React.FC<PlayerCardProps> = ({
  id,
  name,
  aliases,
  analyzed,
  updatedAt,
}) => {
  return (
    <Link to={`/playerbase/${id}`} className="tagger-card">
      <div className="tagger-card-top">
        <span className="tagger-card-title">{name}</span>
        <span className="tagger-chip">Profile</span>
      </div>
      <div className="tagger-card-body">
        <div>
          <span className="tagger-card-label">Analyzed Positions</span>
          <span className="tagger-card-value">{analyzed}</span>
        </div>
        <div>
          <span className="tagger-card-label">Updated</span>
          <span className="tagger-card-value">
            {new Date(updatedAt).toLocaleDateString()}
          </span>
        </div>
      </div>
    </Link>
  );
};

export default PlayerCard;
