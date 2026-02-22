import { useState } from 'react'
import useTeamDiscussion from '../hooks/useTeamDiscussion'

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

export default function TeamDiscussion({ teamName, userId, username }) {
  const { comments, userVotes, loading, error, submitting, postComment, vote, deleteComment } =
    useTeamDiscussion(teamName, userId)

  const [draft, setDraft] = useState('')
  const [postError, setPostError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    const content = draft.trim()
    if (!content) return
    setPostError('')
    try {
      await postComment(content, username)
      setDraft('')
    } catch (err) {
      setPostError(err.message || 'Failed to post comment.')
    }
  }

  return (
    <div className="discussion-section">
      <p className="section-label">Community Discussion</p>

      {userId ? (
        <form className="discussion-form" onSubmit={handleSubmit}>
          <textarea
            className="template-input discussion-textarea"
            placeholder="What do you think about this team?"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={500}
            rows={3}
          />
          <div className="discussion-form-footer">
            <span className="discussion-char-count">{draft.length}/500</span>
            <button
              type="submit"
              className="template-button"
              disabled={submitting || !draft.trim()}
            >
              {submitting ? 'Posting…' : 'Post Comment'}
            </button>
          </div>
          {postError && <p className="template-alert template-alert-error">{postError}</p>}
        </form>
      ) : (
        <p className="discussion-login-prompt">Sign in to join the discussion.</p>
      )}

      {loading && <p className="template-subtitle">Loading comments…</p>}
      {!loading && error && <p className="template-alert template-alert-error">{error}</p>}

      {!loading && !error && comments.length === 0 && (
        <p className="discussion-empty">No comments yet. Be the first!</p>
      )}

      <div className="discussion-list">
        {comments.map((comment) => {
          const myVote = userVotes[comment.id]
          const isOwner = userId === comment.user_id

          return (
            <div key={comment.id} className="discussion-card">
              <div className="discussion-card-header">
                <span className="discussion-username">@{comment.username}</span>
                <span className="discussion-time">{timeAgo(comment.created_at)}</span>
                {isOwner && (
                  <button
                    type="button"
                    className="discussion-delete-btn"
                    onClick={() => deleteComment(comment.id)}
                    title="Delete comment"
                  >
                    ✕
                  </button>
                )}
              </div>

              <p className="discussion-content">{comment.content}</p>

              <div className="discussion-votes">
                <button
                  type="button"
                  className={`discussion-vote-btn ${myVote === 'up' ? 'active-up' : ''}`}
                  onClick={() => vote(comment.id, 'up')}
                  disabled={!userId}
                  title="Upvote"
                >
                  ▲ {comment.upvotes}
                </button>
                <button
                  type="button"
                  className={`discussion-vote-btn ${myVote === 'down' ? 'active-down' : ''}`}
                  onClick={() => vote(comment.id, 'down')}
                  disabled={!userId}
                  title="Downvote"
                >
                  ▼ {comment.downvotes}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
