import { getSupabaseClient } from './supabase'

export async function fetchComments(teamName) {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase
    .from('team_comments')
    .select('*')
    .eq('team_name', teamName)
    .order('created_at', { ascending: false })

  if (error) throw error
  return data ?? []
}

export async function fetchUserVotes(userId, commentIds) {
  if (!commentIds.length) return []
  const supabase = getSupabaseClient()
  const { data, error } = await supabase
    .from('comment_votes')
    .select('comment_id, vote_type')
    .eq('user_id', userId)
    .in('comment_id', commentIds)

  if (error) throw error
  return data ?? []
}

export async function postComment(teamName, userId, username, content) {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase
    .from('team_comments')
    .insert({ team_name: teamName, user_id: userId, username, content })
    .select()
    .single()

  if (error) throw error
  return data
}

export async function deleteComment(commentId) {
  const supabase = getSupabaseClient()
  const { error } = await supabase
    .from('team_comments')
    .delete()
    .eq('id', commentId)

  if (error) throw error
}

// Upserts a vote and syncs the upvotes/downvotes counts on the comment.
// If the user already voted the same way, it removes the vote (toggle off).
export async function submitVote(commentId, userId, voteType) {
  const supabase = getSupabaseClient()

  // Check for existing vote
  const { data: existing } = await supabase
    .from('comment_votes')
    .select('vote_type')
    .eq('comment_id', commentId)
    .eq('user_id', userId)
    .maybeSingle()

  if (existing?.vote_type === voteType) {
    // Same vote → remove it (toggle off)
    await removeVote(commentId, userId)
    return null
  }

  // Remove old vote if switching direction
  if (existing) {
    await supabase
      .from('comment_votes')
      .delete()
      .eq('comment_id', commentId)
      .eq('user_id', userId)
  }

  // Insert new vote
  const { error: voteError } = await supabase
    .from('comment_votes')
    .insert({ comment_id: commentId, user_id: userId, vote_type: voteType })

  if (voteError) throw voteError

  // Recalculate counts
  await _syncVoteCounts(commentId)
  return voteType
}

export async function removeVote(commentId, userId) {
  const supabase = getSupabaseClient()
  const { error } = await supabase
    .from('comment_votes')
    .delete()
    .eq('comment_id', commentId)
    .eq('user_id', userId)

  if (error) throw error
  await _syncVoteCounts(commentId)
}

async function _syncVoteCounts(commentId) {
  const supabase = getSupabaseClient()

  const { data: votes } = await supabase
    .from('comment_votes')
    .select('vote_type')
    .eq('comment_id', commentId)

  const upvotes = votes?.filter((v) => v.vote_type === 'up').length ?? 0
  const downvotes = votes?.filter((v) => v.vote_type === 'down').length ?? 0

  await supabase
    .from('team_comments')
    .update({ upvotes, downvotes })
    .eq('id', commentId)
}
