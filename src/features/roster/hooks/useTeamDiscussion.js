import { useCallback, useEffect, useState } from 'react'
import {
  deleteComment as apiDeleteComment,
  fetchComments,
  fetchUserVotes,
  postComment as apiPostComment,
  submitVote,
} from '../../../lib/discussion'

export default function useTeamDiscussion(teamName, userId) {
  const [comments, setComments] = useState([])
  const [userVotes, setUserVotes] = useState({}) // { [commentId]: 'up' | 'down' }
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadComments = useCallback(async () => {
    if (!teamName) return
    setLoading(true)
    setError('')
    try {
      const data = await fetchComments(teamName)
      setComments(data)

      if (userId && data.length) {
        const votes = await fetchUserVotes(userId, data.map((c) => c.id))
        const voteMap = {}
        for (const v of votes) voteMap[v.comment_id] = v.vote_type
        setUserVotes(voteMap)
      }
    } catch (err) {
      setError(err.message || 'Failed to load comments.')
    } finally {
      setLoading(false)
    }
  }, [teamName, userId])

  useEffect(() => {
    loadComments()
  }, [loadComments])

  const postComment = useCallback(async (content, username) => {
    if (!userId) return
    setSubmitting(true)
    try {
      const newComment = await apiPostComment(teamName, userId, username, content)
      setComments((prev) => [newComment, ...prev])
    } catch (err) {
      throw err
    } finally {
      setSubmitting(false)
    }
  }, [teamName, userId])

  const vote = useCallback(async (commentId, voteType) => {
    if (!userId) return

    const prevComments = comments
    const prevVotes = userVotes
    const currentVote = userVotes[commentId]

    // Optimistic update
    setComments((prev) =>
      prev.map((c) => {
        if (c.id !== commentId) return c
        let { upvotes, downvotes } = c

        if (currentVote === voteType) {
          // Toggle off
          if (voteType === 'up') upvotes -= 1
          else downvotes -= 1
        } else {
          // Remove old vote if switching
          if (currentVote === 'up') upvotes -= 1
          if (currentVote === 'down') downvotes -= 1
          // Add new vote
          if (voteType === 'up') upvotes += 1
          else downvotes += 1
        }
        return { ...c, upvotes, downvotes }
      })
    )

    setUserVotes((prev) => {
      if (prev[commentId] === voteType) {
        const next = { ...prev }
        delete next[commentId]
        return next
      }
      return { ...prev, [commentId]: voteType }
    })

    try {
      await submitVote(commentId, userId, voteType)
    } catch {
      // Rollback on error
      setComments(prevComments)
      setUserVotes(prevVotes)
    }
  }, [comments, userVotes, userId])

  const deleteComment = useCallback(async (commentId) => {
    const prevComments = comments
    setComments((prev) => prev.filter((c) => c.id !== commentId))
    try {
      await apiDeleteComment(commentId)
    } catch {
      setComments(prevComments)
    }
  }, [comments])

  return { comments, userVotes, loading, error, submitting, postComment, vote, deleteComment }
}
