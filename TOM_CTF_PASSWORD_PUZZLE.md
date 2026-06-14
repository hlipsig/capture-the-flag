# The Password Puzzle for Tom 🎭

**CTF Player**: Tom (loves classic literature & economics)

---

## 🎯 Real Password (Obscure Literary Reference)

### **`i_would_prefer_not_to`**

**Source**: Herman Melville's *"Bartleby, the Scrivener"* (1853)

**Context**: Bartleby's famous phrase of passive resistance. When asked to do anything, he responds: "I would prefer not to."

**Why it's perfect for Tom**:
- Classic American literature (19th century)
- Obscure enough that generic password lists won't have it
- The phrase itself is about non-compliance/refusal - thematically appropriate for a security honeypot
- Hint in the notes file: "Bartleby would understand" and "The scrivener's choice is the correct one"

---

## 🎭 Decoy Passwords (Red Herrings)

### 1. **`Hi_TOM!`**
- **Too obvious** - his name
- **Location**: Will appear in `/etc/motd` on honeypot
- **Purpose**: First thing players check, immediate rejection

### 2. **`invisible_hand_1776`**
- **Economics reference**: Adam Smith's "invisible hand" metaphor
- **Location**: Will be in Redis cache key
- **Purpose**: Plays to Tom's economics interest, but still a decoy
- **Year**: 1776 = "The Wealth of Nations" publication date

### 3. **`creative_destruction`**
- **Economics reference**: Joseph Schumpeter's concept
- **Location**: Will be in `.bash_history` on honeypot
- **Purpose**: Another economics bait for Tom

### 4. **`wealth_of_nations`**
- **Economics reference**: Adam Smith's famous book
- **Location**: Fake admin panel HTML comment
- **Purpose**: Most obvious economics reference

### 5. **`mirror_reflect_6789`**
- **Generic looking** - appears like a default password
- **Location**: In `/tmp/backup_config.txt`
- **Purpose**: Looks "official" but still wrong

---

## 📍 Where Tom Finds the Real Password

### Primary Location: `/home/admin/.notes`

```
=== Admin Notes ===
Last updated: 2026-06-04

Mirror Dossier Archive Access:
- URL: http://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io
- Username: ctf
- Password: i_would_prefer_not_to

Bartleby would understand.

---
Other passwords to try (if first doesn't work):
- Hi_TOM!
- invisible_hand_1776
- creative_destruction
- wealth_of_nations

The scrivener's choice is the correct one.
```

**Literary Hints**:
- "Bartleby would understand" - Direct hint to the story
- "The scrivener's choice" - Bartleby was a scrivener (law copyist)
- All decoys are listed to test if he tries them all

---

## 🎮 Expected Player Journey

### Stage 1: Reconnaissance
1. Tom scans target → Gets redirected to honeypot
2. Brute forces SSH → Gets into Cowrie honeypot
3. Explores filesystem

### Stage 2: Password Discovery
1. Finds `/home/admin/.notes` file
2. Sees list of 5 passwords + literary hints
3. Tries obvious ones first:
   - `Hi_TOM!` ❌
   - `wealth_of_nations` ❌ (economics = his interest)
   - `invisible_hand_1776` ❌

### Stage 3: The Epiphany
1. Re-reads the hints: "Bartleby would understand", "scrivener's choice"
2. If Tom knows the story: **immediate recognition**
3. If Tom doesn't: Googles "Bartleby scrivener" → finds famous phrase
4. Tries `i_would_prefer_not_to` ✅

### Stage 4: Accessing Dossier
1. Navigates to `http://dossiers-cyber-riposte.apps.uu7a1hfd.eastus.aroapp.io`
2. HTTP Basic Auth prompts for credentials
3. Username: `ctf`, Password: `i_would_prefer_not_to`
4. **Success!** Sees list of all detected incidents

### Stage 5: The Flag
1. Browses incident list
2. **Sees his own IP address** in the list
3. Realizes: "They scanned me back!"
4. Clicks on his own incident
5. **Flag appears**: `flag{RIPOSTE_COUNTER_RECONNAISSANCE_abc123def}`

---

## 🧩 Why This Works

### For a Literature Enthusiast:
- ✅ Recognizes "Bartleby, the Scrivener" immediately
- ✅ Appreciates the thematic irony (passive resistance in a security context)
- ✅ Feels rewarded for domain knowledge

### For Someone Who Doesn't Know the Story:
- ✅ "Bartleby scrivener" is specific enough to Google
- ✅ Famous phrase appears in top search results
- ✅ Still solvable, just requires research

### Security Perspective:
- ✅ Not in common password dictionaries
- ✅ Not in rockyou.txt or SecLists
- ✅ Requires understanding the hint (social engineering)
- ✅ Can't be brute-forced practically

---

## 🎨 Literary Easter Eggs

### Additional hints Tom might discover:

**In honeypot `/etc/motd`**:
```
"I prefer not to." — A certain Wall Street scrivener

Try: Hi_TOM! if you must.
```

**In fake `README.txt`**:
```
Password policy: Must reference 19th century American literature.
Hint: What would a copyist who refuses to copy say?
```

**In `/var/log/auth.log` (fake entry)**:
```
Failed password for user 'bartleby' from 192.0.2.1
Failed password for user 'scrivener' from 192.0.2.1
```

---

## 🔐 Configuration Summary

| Component | Value | Status |
|-----------|-------|--------|
| **Real Password** | `i_would_prefer_not_to` | ✅ Set in K8s Secret |
| **Dossier URL** | `dossiers-cyber-riposte.apps...` | ✅ OpenShift Route created |
| **Username** | `ctf` | ✅ Hardcoded in web_dossier.py |
| **Hint File** | `/home/admin/.notes` | ✅ Created |
| **Literary Source** | Melville's Bartleby | ✅ Thematically perfect |

---

## 🎓 Educational Value

This puzzle teaches:
1. **Social Engineering**: Reading contextual clues
2. **OSINT**: Researching literary references
3. **Pattern Recognition**: Distinguishing signal from noise
4. **Critical Thinking**: Not just trying every password

And for Tom specifically:
- Rewards his literature knowledge
- Economics decoys are intentional distractions (testing focus)
- The "mirror" concept: The system observing him while he thinks he's observing it

---

**The Mirror**: Where the hunter becomes the hunted, and Bartleby would prefer not to be scanned. 🪞
