import sys

with open("src/services/automation.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Init block
init_target = """        self.current_queue_id: Optional[int] = None"""
init_replacement = """        self.current_queue_id: Optional[int] = None
        self._blacklist = [name.strip().lower() for name in self.config.get("dodge_blacklist", "").split(",") if name.strip()]
        self._toxic_keywords = ["kys", "int", "troll", "run it down", "nword", "f slur"]
        self._chat_warden_warned = False"""
if init_target in content:
    content = content.replace(init_target, init_replacement)
else:
    print("Init target not found")

# 2. handle_champ_select block
champ_target = """        if not session:
            sf = self.stats_func
            if sf is not None:
                sf([], [])
            return"""
champ_replacement = """        if not session:
            sf = self.stats_func
            if sf is not None:
                sf([], [])
            return

        # 2.2 Blacklist Dodging
        self._handle_auto_dodge(session)
        # 2.3 Chat Warden
        self._handle_chat_warden(session)"""
if champ_target in content:
    content = content.replace(champ_target, champ_replacement)
else:
    print("Champ target not found")

# 3. Equip runes block
skin_target = """        # Auto-equip a non-default skin
        if not getattr(self, "_skin_equipped", False):
            self._equip_random_skin(session)

    def _get_local_player(self, session):"""
skin_replacement = """        # Auto-equip a non-default skin
        if not getattr(self, "_skin_equipped", False):
            self._equip_random_skin(session)

        # 2.1 Auto-Equip Runes
        if not getattr(self, "_runes_equipped", False):
            self._auto_equip_runes(session)

    def _get_local_player(self, session):"""
if skin_target in content:
    content = content.replace(skin_target, skin_replacement)
else:
    print("Skin target not found")

# 4. Helper functions addition
synergy_target = """            self._skin_equipped = True

        except Exception as e:
            Logger.error("Auto", f"Skin equip error: {e}")

    def _perform_arena_synergy(self, session):"""
synergy_replacement = """            self._skin_equipped = True

        except Exception as e:
            Logger.error("Auto", f"Skin equip error: {e}")

    def _auto_equip_runes(self, session):
        \"\"\"Inject baseline recommended runes via LCU.\"\"\"
        if not self.config.get("auto_runes_enabled", False):
            self._runes_equipped = True
            return

        try:
            me = self._get_local_player(session)
            if not me: return
            champ_id = me.get("championId", 0)
            if not champ_id: return

            # Get recommended pages
            pos = me.get("assignedPosition", "UTILITY") if me.get("assignedPosition") else "UTILITY"
            req = self.lcu.request("GET", f"/lol-perks/v1/recommended-pages/{champ_id}?position={pos}", silent=True)
            if not req or req.status_code != 200: return
            
            recs = req.json()
            if not recs: return

            best_page = recs[0] # Usually the most popular
            
            apply_res = self.lcu.request("POST", f"/lol-perks/v1/recommended-pages/{champ_id}/apply", data={"pageId": best_page.get("id")}, silent=True)
            if apply_res and apply_res.status_code in [200, 204]:
                self._runes_equipped = True
                self._log("Auto-Equipped Recommended Runes!")
        except Exception as e:
            Logger.debug("Auto", f"Rune equip error: {e}")

    def _handle_auto_dodge(self, session):
        if not getattr(self, "_blacklist", []): return
        
        my_cell = session.get("localPlayerCellId")
        my_team = session.get("myTeam", [])
        
        for p in my_team:
            if p.get("cellId") == my_cell: continue
            
            su_id = p.get("summonerId", 0)
            if not su_id: continue
            
            req = self.lcu.request("GET", f"/lol-summoner/v1/summoners/{su_id}", silent=True)
            if req and req.status_code == 200:
                name = req.json().get("gameName", "").lower()
                tag = req.json().get("tagLine", "").lower()
                full_name = f"{name}#{tag}"
                
                if name in self._blacklist or full_name in self._blacklist:
                    self._log(f"BLACKLIST MATCH: {full_name}. Dodging immediately.")
                    import subprocess
                    subprocess.run(["taskkill", "/IM", "LeagueClient.exe", "/F"], creationflags=subprocess.CREATE_NO_WINDOW)
                    return

    def _handle_chat_warden(self, session):
        chat_room = session.get("chatDetails", {}).get("chatRoomName")
        if not chat_room: return
        
        if getattr(self, "_chat_warden_warned", False): return

        req = self.lcu.request("GET", f"/lol-chat/v1/conversations/{chat_room}/messages", silent=True)
        if not req or req.status_code != 200: return
        
        msgs = req.json()
        for m in msgs:
            text = m.get("body", "").lower()
            for kw in getattr(self, "_toxic_keywords", []):
                if kw in text:
                    self._chat_warden_warned = True
                    self._log(f"Toxicity detected in lobby: '{kw}'")
                    try:
                        from ui.components.toast import ToastManager
                        ToastManager.get_instance().show(f"Toxicity Warning: A teammate typed '{kw}'", theme="error")
                    except: pass
                    return

    def _perform_arena_synergy(self, session):"""
if synergy_target in content:
    content = content.replace(synergy_target, synergy_replacement)
else:
    print("Synergy target not found")

with open("src/services/automation.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Modification complete")
