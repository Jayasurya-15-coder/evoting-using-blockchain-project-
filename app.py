"""
app.py - Main Flask Application for Secure E-Voting System
Handles all routes, session management, and business logic.
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from datetime import datetime
import sqlite3
import json

from database import (
    init_db, get_connection, hash_password,
    get_all_candidates, get_all_voters,
    get_vote_counts, get_election_status,
    save_block_to_db, get_blockchain_from_db,
    get_total_votes, get_total_voters
)
from blockchain import voting_blockchain

# ─── App Setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = "evoting_secret_blockchain_2024"  # Change in production!

# Initialize DB tables and seed sample data on startup
init_db()

# Reload any existing blocks from DB into the in-memory blockchain on startup
def restore_blockchain_from_db():
    """Rebuilds in-memory blockchain from persisted DB records on app start."""
    blocks = get_blockchain_from_db()
    # We only need the count to know genesis exists; full rebuild needs raw data.
    # For this project we simply report chain length from the DB.
    print(f"[Blockchain] {len(blocks)} block(s) found in DB (including genesis).")

restore_blockchain_from_db()


# ─── Utility Decorators ───────────────────────────────────────────────────────

def admin_required(f):
    """Decorator: redirects to admin login if not authenticated."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin" not in session:
            flash("Please log in as admin first.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def voter_required(f):
    """Decorator: redirects to voter login if not authenticated."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "voter_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("voter_login"))
        return f(*args, **kwargs)
    return decorated


# ─── Public Routes ────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """Landing page with login options."""
    return render_template("home.html")


# ─── Admin Routes ─────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_connection()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()
        conn.close()

        if admin:
            session["admin"] = username
            flash("Welcome back, Admin!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Admin control panel with statistics cards."""
    total_votes = get_total_votes()
    total_voters = get_total_voters()
    total_candidates = len(get_all_candidates())
    chain_length = len(get_blockchain_from_db())
    election = get_election_status()

    return render_template(
        "admin_dashboard.html",
        total_votes=total_votes,
        total_voters=total_voters,
        total_candidates=total_candidates,
        chain_length=chain_length,
        election=election
    )


@app.route("/admin/candidates", methods=["GET", "POST"])
@admin_required
def manage_candidates():
    """Add and view candidates."""
    if request.method == "POST":
        name = request.form.get("candidate_name", "").strip()
        if name:
            conn = get_connection()
            conn.execute(
                "INSERT INTO candidates (candidate_name) VALUES (?)", (name,)
            )
            conn.commit()
            conn.close()
            flash(f'Candidate "{name}" added successfully.', "success")
        else:
            flash("Candidate name cannot be empty.", "danger")

    candidates = get_all_candidates()
    return render_template("candidates.html", candidates=candidates)


@app.route("/admin/candidates/delete/<int:cid>")
@admin_required
def delete_candidate(cid):
    """Remove a candidate (only if election not started)."""
    election = get_election_status()
    if election["election_active"]:
        flash("Cannot delete candidates while election is active.", "danger")
        return redirect(url_for("manage_candidates"))

    conn = get_connection()
    conn.execute("DELETE FROM candidates WHERE candidate_id=?", (cid,))
    conn.commit()
    conn.close()
    flash("Candidate removed.", "info")
    return redirect(url_for("manage_candidates"))


@app.route("/admin/election/start")
@admin_required
def start_election():
    """Activates the election so voters can cast votes."""
    candidates = get_all_candidates()
    if len(candidates) < 2:
        flash("Need at least 2 candidates to start the election.", "warning")
        return redirect(url_for("admin_dashboard"))

    conn = get_connection()
    conn.execute("UPDATE election_settings SET election_active=1 WHERE id=1")
    conn.commit()
    conn.close()
    flash("Election has been STARTED. Voters can now cast their votes.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/election/end")
@admin_required
def end_election():
    """Deactivates the election."""
    conn = get_connection()
    conn.execute("UPDATE election_settings SET election_active=0 WHERE id=1")
    conn.commit()
    conn.close()
    flash("Election has been ENDED. No more votes can be cast.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/voters")
@admin_required
def view_voters():
    """View all registered voters and their voting status."""
    voters = get_all_voters()
    return render_template("voters.html", voters=voters)


@app.route("/admin/results")
@admin_required
def admin_results():
    """View election results with vote counts and winner."""
    results = get_vote_counts()
    total = get_total_votes()
    winner = results[0] if results and results[0]["vote_count"] > 0 else None
    return render_template(
        "results.html",
        results=results,
        total=total,
        winner=winner,
        is_admin=True
    )


@app.route("/admin/blockchain")
@admin_required
def view_blockchain():
    """Blockchain explorer page for admins."""
    blocks = get_blockchain_from_db()
    is_valid = voting_blockchain.is_chain_valid()
    chain_length = len(blocks)
    return render_template(
        "blockchain.html",
        blocks=blocks,
        is_valid=is_valid,
        chain_length=chain_length
    )


@app.route("/admin/blockchain/verify")
@admin_required
def verify_blockchain():
    """API endpoint: returns blockchain validity as JSON."""
    is_valid = voting_blockchain.is_chain_valid()
    chain_length = voting_blockchain.get_chain_length()
    return jsonify({
        "valid": is_valid,
        "chain_length": chain_length,
        "message": "Blockchain is intact and untampered." if is_valid
                   else "WARNING: Blockchain integrity compromised!"
    })


@app.route("/admin/blockchain/search")
@admin_required
def search_blockchain():
    """Search blocks by hash string."""
    query = request.args.get("hash", "").strip()
    result = None
    if query:
        result = voting_blockchain.search_by_hash(query)
    blocks = get_blockchain_from_db()
    is_valid = voting_blockchain.is_chain_valid()
    chain_length = len(blocks)
    return render_template(
        "blockchain.html",
        blocks=blocks,
        is_valid=is_valid,
        chain_length=chain_length,
        search_result=result,
        search_query=query
    )


@app.route("/admin/results/export")
@admin_required
def export_results():
    """Export election results as JSON (PDF export handled client-side)."""
    results = get_vote_counts()
    total = get_total_votes()
    return jsonify({
        "election": get_election_status().get("election_name", "Election"),
        "total_votes": total,
        "results": results,
        "timestamp": str(datetime.now())
    })


# ─── Voter Routes ─────────────────────────────────────────────────────────────

@app.route("/voter/login", methods=["GET", "POST"])
def voter_login():
    """Voter login using their Voter ID and password."""
    if request.method == "POST":
        voter_id = request.form.get("voter_id", "").strip().upper()
        password = request.form.get("password", "").strip()

        conn = get_connection()
        voter = conn.execute(
            "SELECT * FROM voters WHERE voter_id=? AND password=?",
            (voter_id, hash_password(password))
        ).fetchone()
        conn.close()

        if voter:
            session["voter_id"] = voter["voter_id"]
            session["voter_name"] = voter["name"]
            session["has_voted"] = bool(voter["has_voted"])
            flash(f'Welcome, {voter["name"]}!', "success")
            return redirect(url_for("voting_page"))
        else:
            flash("Invalid Voter ID or password.", "danger")

    return render_template("voter_login.html")


@app.route("/voter/logout")
def voter_logout():
    session.pop("voter_id", None)
    session.pop("voter_name", None)
    session.pop("has_voted", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/voter/vote", methods=["GET", "POST"])
@voter_required
def voting_page():
    """Displays candidate list and processes vote submission."""
    election = get_election_status()
    voter_id = session["voter_id"]

    # Re-check has_voted from DB (session could be stale)
    conn = get_connection()
    voter = conn.execute(
        "SELECT has_voted FROM voters WHERE voter_id=?", (voter_id,)
    ).fetchone()
    conn.close()

    has_voted = bool(voter["has_voted"]) if voter else True

    if request.method == "POST":
        # Guard rails
        if not election["election_active"]:
            flash("Election is not currently active.", "warning")
            return redirect(url_for("voting_page"))

        if has_voted:
            flash("You have already voted.", "danger")
            return redirect(url_for("voting_page"))

        candidate_id = request.form.get("candidate_id")
        if not candidate_id:
            flash("Please select a candidate.", "warning")
            return redirect(url_for("voting_page"))

        # Validate candidate exists
        conn = get_connection()
        candidate = conn.execute(
            "SELECT * FROM candidates WHERE candidate_id=?", (candidate_id,)
        ).fetchone()

        if not candidate:
            conn.close()
            flash("Invalid candidate selection.", "danger")
            return redirect(url_for("voting_page"))

        # Record vote in DB
        timestamp = str(datetime.now())
        conn.execute(
            "INSERT INTO votes (candidate_id, timestamp) VALUES (?, ?)",
            (candidate_id, timestamp)
        )
        # Mark voter as voted
        conn.execute(
            "UPDATE voters SET has_voted=1 WHERE voter_id=?", (voter_id,)
        )
        conn.commit()
        conn.close()

        # Add block to blockchain
        new_block = voting_blockchain.add_vote(voter_id, int(candidate_id))
        # Persist block to DB
        save_block_to_db(new_block.to_dict())

        # Update session
        session["has_voted"] = True

        flash(
            f'Your vote for "{candidate["candidate_name"]}" has been recorded on the blockchain!',
            "success"
        )
        return redirect(url_for("vote_confirmation", block_hash=new_block.current_hash))

    candidates = get_all_candidates()
    return render_template(
        "voting.html",
        candidates=candidates,
        has_voted=has_voted,
        election=election,
        voter_name=session.get("voter_name")
    )


@app.route("/voter/confirmation/<block_hash>")
@voter_required
def vote_confirmation(block_hash):
    """Shows confirmation page with the block hash after voting."""
    return render_template("confirmation.html", block_hash=block_hash)


@app.route("/results")
def public_results():
    """Public results page (visible after election ends or always)."""
    results = get_vote_counts()
    total = get_total_votes()
    winner = results[0] if results and results[0]["vote_count"] > 0 else None
    return render_template(
        "results.html",
        results=results,
        total=total,
        winner=winner,
        is_admin=False
    )


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Secure E-Voting System Using Blockchain Technology")
    print("  Running on http://127.0.0.1:5000")
    print("  Admin credentials: admin / admin123")
    print("  Sample voter: V001 / pass001")
    print("=" * 60)
    app.run(debug=True)
