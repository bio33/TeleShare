import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # DGSCs table (stored as 'pendrives' for compatibility)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pendrives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                current_owner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_owner_id) REFERENCES users (user_id)
            )
        ''')
        
        # Requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pendrive_id INTEGER NOT NULL,
                requester_id INTEGER NOT NULL,
                current_owner_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (pendrive_id) REFERENCES pendrives (id),
                FOREIGN KEY (requester_id) REFERENCES users (user_id),
                FOREIGN KEY (current_owner_id) REFERENCES users (user_id)
            )
        ''')
        
        # Transaction history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pendrive_id INTEGER NOT NULL,
                from_user_id INTEGER,
                to_user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pendrive_id) REFERENCES pendrives (id),
                FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                FOREIGN KEY (to_user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        """Add or update user information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    def add_dgsc(self, name: str, description: str, owner_id: int) -> bool:
        """Add a new DGSC to the system"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO pendrives (name, description, current_owner_id)
                VALUES (?, ?, ?)
            ''', (name, description, owner_id))
            
            dgsc_id = cursor.lastrowid
            
            # Add initial transaction
            cursor.execute('''
                INSERT INTO transactions (pendrive_id, to_user_id, transaction_type)
                VALUES (?, ?, 'initial_assignment')
            ''', (dgsc_id, owner_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def get_user_dgscs(self, user_id: int) -> List[Tuple]:
        """Get all DGSCs currently owned by a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, created_at
            FROM pendrives
            WHERE current_owner_id = ?
        ''', (user_id,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_all_dgscs(self) -> List[Tuple]:
        """Get all DGSCs in the system with their current owners"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.current_owner_id,
                   u.username, u.first_name, u.last_name, p.created_at
            FROM pendrives p
            LEFT JOIN users u ON p.current_owner_id = u.user_id
            ORDER BY p.created_at DESC
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def search_dgsc(self, search_term: str) -> List[Tuple]:
        """Search for DGSCs by name or description"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.current_owner_id,
                   u.username, u.first_name, u.last_name
            FROM pendrives p
            LEFT JOIN users u ON p.current_owner_id = u.user_id
            WHERE p.name LIKE ? OR p.description LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def create_request(self, dgsc_id: int, requester_id: int, current_owner_id: int, message: str = '') -> int:
        """Create a new request for a DGSC"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requests (pendrive_id, requester_id, current_owner_id, message)
            VALUES (?, ?, ?, ?)
        ''', (dgsc_id, requester_id, current_owner_id, message))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id
    
    def get_pending_requests_for_user(self, user_id: int) -> List[Tuple]:
        """Get all pending requests where user is the current owner"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, r.pendrive_id, p.name, r.requester_id,
                   u.username, u.first_name, r.message, r.created_at
            FROM requests r
            JOIN pendrives p ON r.pendrive_id = p.id
            JOIN users u ON r.requester_id = u.user_id
            WHERE r.current_owner_id = ? AND r.status = 'pending'
        ''', (user_id,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_user_requests(self, user_id: int) -> List[Tuple]:
        """Get all requests made by a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, r.pendrive_id, p.name, r.current_owner_id,
                   u.username, u.first_name, r.status, r.created_at
            FROM requests r
            JOIN pendrives p ON r.pendrive_id = p.id
            JOIN users u ON r.current_owner_id = u.user_id
            WHERE r.requester_id = ?
            ORDER BY r.created_at DESC
        ''', (user_id,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def accept_request(self, request_id: int) -> bool:
        """Accept a request and transfer ownership"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute('''
            SELECT pendrive_id, requester_id, current_owner_id
            FROM requests
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        dgsc_id, requester_id, current_owner_id = result
        
        # Update DGSC ownership
        cursor.execute('''
            UPDATE pendrives
            SET current_owner_id = ?
            WHERE id = ?
        ''', (requester_id, dgsc_id))
        
        # Update request status
        cursor.execute('''
            UPDATE requests
            SET status = 'accepted', resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request_id,))
        
        # Add transaction record
        cursor.execute('''
            INSERT INTO transactions (pendrive_id, from_user_id, to_user_id, transaction_type)
            VALUES (?, ?, ?, 'transfer')
        ''', (dgsc_id, current_owner_id, requester_id))
        
        conn.commit()
        conn.close()
        return True
    
    def reject_request(self, request_id: int) -> bool:
        """Reject a request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE requests
            SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0
    
    def get_dgsc_by_id(self, dgsc_id: int) -> Optional[Tuple]:
        """Get DGSC details by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.current_owner_id,
                   u.username, u.first_name, u.last_name
            FROM pendrives p
            LEFT JOIN users u ON p.current_owner_id = u.user_id
            WHERE p.id = ?
        ''', (dgsc_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result
