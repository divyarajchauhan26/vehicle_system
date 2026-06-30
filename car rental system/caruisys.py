"""
=============================================================
  CAR RENTAL SYSTEM — Desktop UI  (Tkinter)
  Task 5 & 6 — TA / Instructor Demo
  Install : pip install mysql-connector-python
  Run     : python carui.py
=============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import mysql.connector
from mysql.connector import Error
from datetime import date, datetime, timedelta

# ─────────────────────────────────────────────
#  DB CONFIG
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Admin@12",
    "database": "CarRentalSystem"
}

DAILY_RATES = {"SUV": 100, "Sedan": 70, "Hatchback": 50, "Truck": 90}

# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
C = {
    "bg":       "#0F1117",
    "sidebar":  "#161B27",
    "card":     "#1C2333",
    "border":   "#2A3350",
    "accent":   "#3B82F6",
    "accent2":  "#10B981",
    "danger":   "#EF4444",
    "warn":     "#F59E0B",
    "text":     "#E2E8F0",
    "muted":    "#64748B",
    "heading":  "#F8FAFC",
    "row_odd":  "#1C2333",
    "row_even": "#1A2030",
    "sel":      "#2D4A7A",
}

FONT_TITLE = ("Courier New", 13, "bold")
FONT_HEAD  = ("Courier New", 10, "bold")
FONT_BODY  = ("Courier New",  9)
FONT_SMALL = ("Courier New",  8)
FONT_MONO  = ("Courier New",  9)
FONT_BIG   = ("Courier New", 16, "bold")

# ─────────────────────────────────────────────
#  DB HELPERS
# ─────────────────────────────────────────────
def get_conn():
    try:
        c = mysql.connector.connect(**DB_CONFIG)
        if c.is_connected():
            return c
    except Error as e:
        messagebox.showerror("DB Error", str(e))
    return None

def run_query(sql, params=()):
    conn = get_conn()
    if not conn:
        return [], []
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, rows
    except Error as e:
        messagebox.showerror("Query Error", str(e))
        return [], []
    finally:
        cur.close(); conn.close()

def run_write(sql, params=()):
    conn = get_conn()
    if not conn:
        return False, "No DB connection"
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return True, "OK"
    except Error as e:
        return False, e.msg
    finally:
        cur.close(); conn.close()

def record_exists(table, pk_col, pk_val):
    _, rows = run_query(f"SELECT 1 FROM `{table}` WHERE `{pk_col}` = %s", (pk_val,))
    return len(rows) > 0

def next_id(table, pk_col, base=1000, floor=None):
    _, rows = run_query(
        f"SELECT COALESCE(MAX(`{pk_col}`), %s) + 1 FROM `{table}`", (base,))
    val = int(rows[0][0]) if rows else base + 1
    if floor is not None:
        val = max(val, floor + 1)
    return val

# ─────────────────────────────────────────────
#  DATE / DATETIME HELPERS
# ─────────────────────────────────────────────
def parse_date(s):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None

def parse_datetime(s):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:
            pass
    return None

def to_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except Exception:
        return None

def to_datetime(v):
    if isinstance(v, datetime):
        return v
    try:
        return datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

# ─────────────────────────────────────────────
#  BUSINESS LOGIC
# ─────────────────────────────────────────────
def vehicle_overlap_check(vid, start_str, end_str, exclude_res_id=None):
    sql = """
        SELECT reservation_id, start_date, end_date
        FROM   RESERVATION
        WHERE  vehicle_id  = %s
          AND  status      = 'CONFIRMED'
          AND  start_date <= %s
          AND  end_date   >= %s
    """
    params = [vid, end_str, start_str]
    if exclude_res_id:
        sql += " AND reservation_id != %s"
        params.append(exclude_res_id)
    _, rows = run_query(sql, tuple(params))
    return rows

def customer_overlap_check(cust_id, start_str, end_str, exclude_res_id=None):
    sql = """
        SELECT reservation_id, vehicle_id, start_date, end_date
        FROM   RESERVATION
        WHERE  customer_id = %s
          AND  status      = 'CONFIRMED'
          AND  start_date <= %s
          AND  end_date   >= %s
    """
    params = [cust_id, end_str, start_str]
    if exclude_res_id:
        sql += " AND reservation_id != %s"
        params.append(exclude_res_id)
    _, rows = run_query(sql, tuple(params))
    return rows

def customer_doc_status(cust_id):
    _, docs = run_query(
        "SELECT document_type, status, expiry_date "
        "FROM DOCUMENT WHERE customer_id = %s",
        (cust_id,))
    _, valid = run_query(
        "SELECT 1 FROM DOCUMENT "
        "WHERE customer_id = %s AND status = 'VERIFIED' "
        "AND expiry_date >= CURDATE() LIMIT 1",
        (cust_id,))
    return len(valid) > 0, docs

def get_daily_rate(category):
    return DAILY_RATES.get(category, 65)

def calc_charge(category, disc_pct, pickup_dt, return_dt):
    rate       = get_daily_rate(category)
    disc       = float(disc_pct or 0) / 100.0
    eff        = rate * (1.0 - disc)
    total_days = max((return_dt.date() - pickup_dt.date()).days, 1)
    
    return {
        "rate":      rate,
        "disc_pct":  disc_pct,
        "eff":       eff,
        "days":      total_days,
        "total":     total_days * eff,
    }

def get_balance(rental_id):
    _, tr = run_query("SELECT total_amount FROM RENTAL WHERE rental_id = %s", (rental_id,))
    total = float(tr[0][0]) if tr and tr[0][0] is not None else 0.0
    _, pr = run_query(
        "SELECT COALESCE(SUM(amount),0) FROM PAYMENT "
        "WHERE rental_id = %s AND status = 'COMPLETED'", (rental_id,))
    paid = float(pr[0][0]) if pr else 0.0
    return total, paid, max(total - paid, 0.0)

# ─────────────────────────────────────────────
#  DROPDOWN LOADERS
# ─────────────────────────────────────────────
_EM = "\u2014"

def _em(pk, label):
    return f"{pk} {_EM} {label}"

def load_customers():
    _, r = run_query(
        "SELECT customer_id, CONCAT(first_name,' ',last_name) "
        "FROM CUSTOMER ORDER BY customer_id")
    return [_em(x[0], x[1]) for x in r]

def load_vehicles_available():
    _, r = run_query(
        "SELECT vehicle_id, model, category FROM VEHICLE "
        "WHERE status = 'AVAILABLE' ORDER BY vehicle_id")
    return [_em(x[0], f"{x[1]} ({x[2]})") for x in r]

def load_vehicles_all_no_status():
    _, r = run_query(
        "SELECT vehicle_id, model, category FROM VEHICLE ORDER BY vehicle_id")
    return [_em(x[0], f"{x[1]} ({x[2]})") for x in r]

def load_branches():
    _, r = run_query(
        "SELECT branch_id, branch_name FROM BRANCH ORDER BY branch_id")
    return [_em(x[0], x[1]) for x in r]

def load_res_confirmed():
    _, r = run_query("""
        SELECT r.reservation_id,
               CONCAT(c.first_name,' ',c.last_name),
               r.vehicle_id, r.start_date, r.end_date
        FROM   RESERVATION r
        JOIN   CUSTOMER c ON r.customer_id = c.customer_id
        WHERE  r.status = 'CONFIRMED'
        ORDER  BY r.reservation_id
    """)
    return [_em(x[0], f"{x[1]} | Veh#{x[2]} ({str(x[3])[:10]}→{str(x[4])[:10]})") for x in r]

def load_res_all():
    _, r = run_query(
        "SELECT reservation_id, customer_id, vehicle_id, status "
        "FROM RESERVATION ORDER BY reservation_id DESC")
    return [_em(x[0], f"Cust#{x[1]} | Veh#{x[2]} ({x[3]})") for x in r]

def load_rentals_active():
    _, r = run_query("""
        SELECT r.rental_id, v.model,
               CONCAT(c.first_name,' ',c.last_name), r.pickup_date
        FROM   RENTAL r
        JOIN   VEHICLE v     ON r.vehicle_id      = v.vehicle_id
        JOIN   RESERVATION s ON r.reservation_id  = s.reservation_id
        JOIN   CUSTOMER c    ON s.customer_id     = c.customer_id
        WHERE  r.status = 'ACTIVE'
        ORDER  BY r.rental_id
    """)
    return [_em(x[0], f"{x[1]} | {x[2]} | {str(x[3])[:10]}") for x in r]

def load_rentals_all():
    _, r = run_query("""
        SELECT r.rental_id, v.model,
               CONCAT(c.first_name,' ',c.last_name), r.status
        FROM   RENTAL r
        JOIN   VEHICLE v     ON r.vehicle_id      = v.vehicle_id
        JOIN   RESERVATION s ON r.reservation_id  = s.reservation_id
        JOIN   CUSTOMER c    ON s.customer_id     = c.customer_id
        ORDER  BY r.rental_id DESC
    """)
    return [_em(x[0], f"{x[1]} | {x[2]} ({x[3]})") for x in r]

PAYMENT_TYPES = ["Credit Card", "Debit Card", "Cash", "Bank Transfer", "UPI"]

def get_id(val):
    if val and _EM in val:
        return val.split(_EM)[0].strip()
    return val.strip() if val else ""

# ─────────────────────────────────────────────
#  VALIDATION HELPERS
# ─────────────────────────────────────────────
def validate_reservation(log, cid, vid, st_raw, en_raw):
    if not cid:
        log_write(log, "  ✗  Please select a Customer.", "err");  return None, None
    if not vid:
        log_write(log, "  ✗  Please select a Vehicle.", "err");   return None, None
    if not st_raw:
        log_write(log, "  ✗  Start Date is required.  Format: YYYY-MM-DD", "err"); return None, None
    if not en_raw:
        log_write(log, "  ✗  End Date is required.  Format: YYYY-MM-DD", "err");   return None, None

    st = parse_date(st_raw)
    if st is None:
        log_write(log, f"  ✗  '{st_raw}' is not a valid date. Use YYYY-MM-DD", "err")
        return None, None

    en = parse_date(en_raw)
    if en is None:
        log_write(log, f"  ✗  '{en_raw}' is not a valid date. Use YYYY-MM-DD", "err")
        return None, None

    if en < st:
        log_write(log, "  ✗  End Date cannot be before Start Date.", "err")
        log_write(log, f"        Start: {st}   End: {en}", "err"); return None, None
    if en == st:
        log_write(log, "  ✗  Minimum rental period is 1 day (End must be after Start).", "err")
        return None, None
    if st < date.today():
        log_write(log, f"  ⚠  Start Date {st} is in the past.", "warn")

    if not record_exists("CUSTOMER", "customer_id", cid):
        log_write(log, f"  ✗  Customer #{cid} not found in DB.", "err"); return None, None
    if not record_exists("VEHICLE", "vehicle_id", vid):
        log_write(log, f"  ✗  Vehicle #{vid} not found in DB.", "err"); return None, None

    cust_conflicts = customer_overlap_check(cid, st_raw, en_raw)
    if cust_conflicts:
        log_write(log, "  ══" * 22, "err")
        log_write(log, "  ✗  CUSTOMER DOUBLE-BOOKING PREVENTED", "err")
        log_write(log, f"     Customer #{cid} already has a CONFIRMED reservation", "err")
        log_write(log, "     whose dates overlap the requested period:", "err")
        for row in cust_conflicts:
            log_write(log,
                f"        Res #{row[0]}  |  Vehicle #{row[1]}  "
                f"|  {str(row[2])[:10]} → {str(row[3])[:10]}", "err")
        log_write(log, "     Choose different dates or a different customer.", "err")
        log_write(log, "  ══" * 22, "err")
        return None, None

    return st, en

def validate_rental_start(log, res_id, bid, dt_raw):
    if not res_id:
        log_write(log, "  ✗  Please select a Reservation.", "err"); return None
    if not bid:
        log_write(log, "  ✗  Please select a Pickup Branch.", "err"); return None
    if not dt_raw:
        log_write(log, "  ✗  Pickup DateTime is required.", "err"); return None

    dt = parse_datetime(dt_raw)
    if dt is None:
        log_write(log, f"  ✗  '{dt_raw}' is not a valid datetime.", "err")
        log_write(log, "        Use YYYY-MM-DD HH:MM:SS   e.g. 2026-04-01 10:00:00", "err")
        return None

    if not record_exists("RESERVATION", "reservation_id", res_id):
        log_write(log, f"  ✗  Reservation #{res_id} not found.", "err"); return None
    if not record_exists("BRANCH", "branch_id", bid):
        log_write(log, f"  ✗  Branch #{bid} not found.", "err"); return None
    return dt

def validate_rental_end(log, rid, bid, dt_raw):
    if not rid:
        log_write(log, "  ✗  Please select an Active Rental.", "err"); return None, None, None
    if not bid:
        log_write(log, "  ✗  Please select a Return Branch.", "err");  return None, None, None
    if not dt_raw:
        log_write(log, "  ✗  Return DateTime is required.", "err");    return None, None, None

    ret_dt = parse_datetime(dt_raw)
    if ret_dt is None:
        log_write(log, f"  ✗  '{dt_raw}' is not a valid datetime.", "err")
        log_write(log, "        Use YYYY-MM-DD HH:MM:SS   e.g. 2026-04-05 15:00:00", "err")
        return None, None, None

    if not record_exists("RENTAL", "rental_id", rid):
        log_write(log, f"  ✗  Rental #{rid} not found.", "err"); return None, None, None
    if not record_exists("BRANCH", "branch_id", bid):
        log_write(log, f"  ✗  Branch #{bid} not found.", "err"); return None, None, None

    _, r = run_query(
        "SELECT status, vehicle_id, pickup_date FROM RENTAL WHERE rental_id = %s", (rid,))
    if not r:
        log_write(log, "  ✗  Could not read rental row.", "err"); return None, None, None

    rstatus, veh_id, pickup_raw = r[0]
    if rstatus != "ACTIVE":
        log_write(log, f"  ✗  Rental #{rid} is '{rstatus}'. Only ACTIVE rentals can be completed.", "err")
        return None, None, None

    pickup_dt = to_datetime(pickup_raw)
    if pickup_dt and ret_dt <= pickup_dt:
        log_write(log, "  ✗  Return DateTime must be AFTER Pickup DateTime.", "err")
        log_write(log, f"        Pickup : {pickup_dt}", "err")
        log_write(log, f"        Return : {ret_dt}", "err")
        return None, None, None

    return ret_dt, veh_id, pickup_dt

# ─────────────────────────────────────────────
#  WIDGET FACTORY HELPERS
# ─────────────────────────────────────────────
def card_frame(parent, padx=8, pady=8, bg=None):
    return tk.Frame(parent, bg=bg or C["card"], padx=padx, pady=pady)

def label(parent, text, font=FONT_BODY, fg=None, bg=None, **kw):
    kw.pop("fg", None); kw.pop("bg", None)
    return tk.Label(parent, text=text, font=font,
                    fg=fg or C["text"], bg=bg or C["card"], **kw)

def heading(parent, text, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text, font=FONT_TITLE,
                    fg=fg or C["heading"], bg=bg or C["card"], **kw)

def btn(parent, text, cmd, color=None, width=18, **kw):
    b = tk.Button(parent, text=text, command=cmd,
                  font=FONT_HEAD,
                  bg=color or C["accent"], fg=C["heading"],
                  activebackground=C["border"], activeforeground=C["heading"],
                  relief="flat", cursor="hand2", width=width, pady=6, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=C["border"]))
    b.bind("<Leave>", lambda e: b.config(bg=color or C["accent"]))
    return b

def entry(parent, width=26, **kw):
    return tk.Entry(parent, font=FONT_BODY,
                    bg=C["border"], fg=C["text"],
                    insertbackground=C["text"],
                    relief="flat", width=width, **kw)

def _apply_combo_style():
    s = ttk.Style()
    s.configure("Car.TCombobox",
                fieldbackground=C["border"], background=C["border"],
                foreground=C["text"], selectbackground=C["sel"],
                selectforeground=C["heading"], arrowcolor=C["accent"])
    s.map("Car.TCombobox",
          fieldbackground=[("readonly", C["border"]), ("disabled", C["bg"])],
          foreground=[("readonly", C["text"])])

def combo(parent, loader, width=34, **kw):
    _apply_combo_style()
    cb = ttk.Combobox(parent, font=FONT_BODY, width=width,
                      style="Car.TCombobox", **kw)
    cb["values"] = loader()
    def _refresh(event=None):
        cur = cb.get()
        cb["values"] = loader()
        if cur:
            cb.set(cur)
    cb.bind("<Button-1>", _refresh)
    cb.bind("<FocusIn>",  _refresh)
    return cb

def combo_row(parent, lbl_text, row, loader, col=0, width=34):
    label(parent, lbl_text + ":", bg=C["card"]).grid(
        row=row, column=col, sticky="w", padx=(0, 8), pady=4)
    cb = combo(parent, loader, width=width)
    cb.grid(row=row, column=col + 1, sticky="w", pady=4)
    return cb

def static_combo_row(parent, lbl_text, row, values, col=0, width=28):
    _apply_combo_style()
    label(parent, lbl_text + ":", bg=C["card"]).grid(
        row=row, column=col, sticky="w", padx=(0, 8), pady=4)
    cb = ttk.Combobox(parent, font=FONT_BODY, width=width,
                      style="Car.TCombobox", values=values)
    cb.grid(row=row, column=col + 1, sticky="w", pady=4)
    return cb

def form_row(parent, lbl_text, row, col=0, w=25):
    label(parent, lbl_text + ":", bg=C["card"]).grid(
        row=row, column=col, sticky="w", padx=(0, 8), pady=4)
    e = entry(parent, width=w)
    e.grid(row=row, column=col + 1, sticky="w", pady=4)
    return e

def hint_row(parent, text, row, col=1):
    label(parent, "  " + text, font=FONT_SMALL,
          fg=C["muted"], bg=C["card"]).grid(row=row, column=col, sticky="w")

def db_hint_row(parent, row=0):
    label(parent,
          "  ↓  Click any dropdown to auto-refresh from DB",
          font=FONT_SMALL, fg=C["muted"], bg=C["card"]).grid(
          row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))

def divider(parent, pady=6):
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=pady)

def make_tree(parent, cols, heights=12):
    style = ttk.Style(); style.theme_use("clam")
    style.configure("Car.Treeview",
                    background=C["row_odd"], foreground=C["text"],
                    fieldbackground=C["row_odd"], rowheight=24, font=FONT_BODY)
    style.configure("Car.Treeview.Heading",
                    background=C["border"], foreground=C["accent"],
                    font=FONT_HEAD, relief="flat")
    style.map("Car.Treeview",
              background=[("selected", C["sel"])],
              foreground=[("selected", C["heading"])])
    frame = tk.Frame(parent, bg=C["card"])
    tree  = ttk.Treeview(frame, columns=cols, show="headings",
                         style="Car.Treeview", height=heights)
    vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=max(len(col) * 11, 80), anchor="w")
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
    return frame, tree

def populate_tree(tree, cols, rows):
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        vals = [str(v) if v is not None else "NULL" for v in row]
        tag  = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=vals, tags=(tag,))
    tree.tag_configure("even", background=C["row_even"])
    tree.tag_configure("odd",  background=C["row_odd"])

def log_box(parent, height=8):
    tb = scrolledtext.ScrolledText(
        parent, height=height, font=FONT_MONO,
        bg=C["bg"], fg=C["text"], insertbackground=C["text"],
        relief="flat", wrap="word", state="disabled")
    tb.tag_config("ok",      foreground=C["accent2"])
    tb.tag_config("err",     foreground=C["danger"])
    tb.tag_config("warn",    foreground=C["warn"])
    tb.tag_config("info",    foreground=C["accent"])
    tb.tag_config("heading", foreground=C["heading"], font=FONT_HEAD)
    return tb

def log_write(tb, text, tag="info"):
    tb.config(state="normal")
    tb.insert("end", text + "\n", tag)
    tb.see("end")
    tb.config(state="disabled")

def log_clear(tb):
    tb.config(state="normal")
    tb.delete("1.0", "end")
    tb.config(state="disabled")

def info_block_grid(parent, row, title, fields):
    f = tk.Frame(parent, bg=C["border"], padx=12, pady=10)
    f.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
    tk.Label(f, text=title, font=FONT_HEAD,
             fg=C["warn"], bg=C["border"]).pack(anchor="w", pady=(0, 6))
    for lbl, var, clr in fields:
        row2 = tk.Frame(f, bg=C["border"]); row2.pack(fill="x", pady=1)
        tk.Label(row2, text=lbl, font=FONT_SMALL, fg=C["muted"],
                 bg=C["border"], width=18, anchor="w").pack(side="left")
        tk.Label(row2, textvariable=var, font=FONT_MONO,
                 fg=clr, bg=C["border"]).pack(side="left", padx=4)
    return f

def make_scrollable(parent, bg=None):
    bg = bg or C["bg"]
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_inner_configure(e):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(e):
        canvas.itemconfig(win_id, width=e.width)

    inner.bind("<Configure>", _on_inner_configure)
    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.configure(yscrollcommand=vsb.set)

    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    def _mw(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    def _mw_linux_up(e):
        canvas.yview_scroll(-1, "units")
    def _mw_linux_down(e):
        canvas.yview_scroll(1, "units")

    def _bind(e):
        canvas.bind_all("<MouseWheel>",  _mw)
        canvas.bind_all("<Button-4>",    _mw_linux_up)
        canvas.bind_all("<Button-5>",    _mw_linux_down)
    def _unbind(e):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind)
    canvas.bind("<Leave>", _unbind)
    return inner

# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class CarRentalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Car Rental Management System — Task 5 & 6 Demo")
        self.geometry("1380x840")
        self.minsize(1100, 700)
        self.configure(bg=C["bg"])
        self._build()
        self._show("dashboard")

    def _build(self):
        self.sidebar = tk.Frame(self, bg=C["sidebar"], width=215)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.main = tk.Frame(self, bg=C["bg"])
        self.main.pack(side="left", fill="both", expand=True)
        self.status_var = tk.StringVar(value="◉  Connected to CarRentalSystem")
        tk.Label(self, textvariable=self.status_var,
                 font=FONT_SMALL, bg=C["border"], fg=C["muted"],
                 anchor="w", padx=10).pack(side="bottom", fill="x")

        self._build_sidebar()
        self.container = tk.Frame(self.main, bg=C["bg"])
        self.container.pack(fill="both", expand=True, padx=12, pady=12)

        self.panels = {}
        builders = [
            ("dashboard",   self._panel_dashboard),
            ("cars",        self._panel_cars),
            ("customers",   self._panel_customers),
            ("reservation", self._panel_reservation),
            ("start",       self._panel_start),
            ("end",         self._panel_end),
            ("payment",     self._panel_payment),
            ("active",      self._panel_active),
            ("revenue",     self._panel_revenue),
            ("triggers",    self._panel_triggers),
            ("transactions", self._panel_transactions), # Added Task 6 Panel
        ]
        for key, builder in builders:
            self.panels[key] = builder()

    def _build_sidebar(self):
        tk.Label(self.sidebar, text="🚗 CAR RENTAL",
                 font=("Courier New", 12, "bold"),
                 fg=C["accent"], bg=C["sidebar"], pady=18).pack(fill="x")
        tk.Label(self.sidebar, text="MGMT SYSTEM",
                 font=FONT_SMALL, fg=C["muted"], bg=C["sidebar"]).pack()
        tk.Frame(self.sidebar, bg=C["border"], height=1).pack(fill="x", pady=10)

        nav = [
            ("⬡  Dashboard",        "dashboard"),
            ("◈  Available Cars",    "cars"),
            ("◉  Customers & Docs",  "customers"),
            ("◎  Make Reservation",  "reservation"),
            ("▶  Start Rental",      "start"),
            ("■  Complete Rental",   "end"),
            ("$  Record Payment",    "payment"),
            ("≡  Active Rentals",    "active"),
            ("◈  Revenue Report",    "revenue"),
        ]
        self._nav_btns = {}
        for txt, key in nav:
            b = tk.Button(self.sidebar, text=txt, font=FONT_BODY,
                          bg=C["sidebar"], fg=C["text"],
                          activebackground=C["card"], activeforeground=C["heading"],
                          relief="flat", anchor="w", padx=18, pady=8, cursor="hand2",
                          command=lambda k=key: self._show(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        tk.Frame(self.sidebar, bg=C["border"], height=1).pack(fill="x", pady=10)
        
        # Trigger Demo Button
        tb = tk.Button(self.sidebar, text="⚡ TRIGGER DEMO",
                       font=FONT_HEAD, bg=C["warn"], fg=C["bg"],
                       activebackground=C["accent2"], relief="flat",
                       anchor="w", padx=18, pady=10, cursor="hand2",
                       command=lambda: self._show("triggers"))
        tb.pack(fill="x", padx=8, pady=4)
        self._nav_btns["triggers"] = tb

        # Task 6 Transactions Demo Button
        txb = tk.Button(self.sidebar, text="🔄 TRANSACTIONS",
                       font=FONT_HEAD, bg=C["accent2"], fg=C["bg"],
                       activebackground=C["warn"], relief="flat",
                       anchor="w", padx=18, pady=10, cursor="hand2",
                       command=lambda: self._show("transactions"))
        txb.pack(fill="x", padx=8, pady=4)
        self._nav_btns["transactions"] = txb

    def _show(self, key):
        for p in self.panels.values():
            p.pack_forget()
        self.panels[key].pack(fill="both", expand=True)
        for k, b in self._nav_btns.items():
            if k == "triggers":
                b.config(bg=C["warn"] if key == k else C["sidebar"], fg=C["bg"] if key == k else C["text"])
            elif k == "transactions":
                b.config(bg=C["accent2"] if key == k else C["sidebar"], fg=C["bg"] if key == k else C["text"])
            else:
                b.config(bg=C["accent"] if key == k else C["sidebar"], fg=C["heading"] if key == k else C["text"])
        self.status_var.set(f"◉  Viewing: {key.replace('_',' ').title()}")

    # ─────────────────────────────────────────
    #  DASHBOARD
    # ─────────────────────────────────────────
    def _panel_dashboard(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "CAR RENTAL MANAGEMENT SYSTEM",
                fg=C["accent"], bg=C["bg"]).pack(pady=(10, 2))
        label(p, "Task 5 & 6 — TA / Instructor Demo Interface",
              fg=C["muted"], bg=C["bg"]).pack(pady=(0, 20))

        sf = tk.Frame(p, bg=C["bg"]); sf.pack(fill="x", pady=10)
        self._stat_vars = {}
        stats = [
            ("Customers",      "SELECT COUNT(*) FROM CUSTOMER",                      C["accent"]),
            ("Vehicles",       "SELECT COUNT(*) FROM VEHICLE",                       C["accent2"]),
            ("Reservations",   "SELECT COUNT(*) FROM RESERVATION",                   C["warn"]),
            ("Active Rentals", "SELECT COUNT(*) FROM RENTAL WHERE status='ACTIVE'", C["danger"]),
        ]
        for i, (title, sql, color) in enumerate(stats):
            card = tk.Frame(sf, bg=C["card"], padx=20, pady=14)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            sf.columnconfigure(i, weight=1)
            v = tk.StringVar(value="…")
            self._stat_vars[title] = (v, sql)
            tk.Label(card, textvariable=v, font=FONT_BIG,
                     fg=color, bg=C["card"]).pack()
            tk.Label(card, text=title, font=FONT_SMALL,
                     fg=C["muted"], bg=C["card"]).pack()

        btn(p, "🔄  Refresh Stats", self._refresh_dashboard,
            width=22).pack(pady=14)

        info = tk.Frame(p, bg=C["card"], padx=20, pady=16)
        info.pack(fill="x", padx=4, pady=8)
        label(info, "TRIGGERS & RULES IMPLEMENTED", font=FONT_HEAD,
              fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Frame(info, bg=C["border"], height=1).pack(fill="x", pady=6)
        tdata = [
            ("T1",  "BEFORE INSERT → RESERVATION", "Blocks overlapping date bookings for the same vehicle"),
            ("T2",  "BEFORE INSERT → RENTAL",      "Blocks rental if customer has NO valid, unexpired VERIFIED document"),
            ("T3",  "AFTER INSERT  → RENTAL",      "Auto-sets vehicle status → RENTED on pickup"),
            ("T4",  "AFTER UPDATE  → RENTAL",      "Auto-sets vehicle status → AVAILABLE on return"),
            ("★",   "APP RULE — RESERVATION",      "Customer double-booking blocked — no two overlapping reservations per customer"),
        ]
        for tid, event, desc in tdata:
            rf = tk.Frame(info, bg=C["card"]); rf.pack(fill="x", pady=2)
            clr = C["accent2"] if tid == "★" else C["warn"]
            tk.Label(rf, text=f"  {tid} ", font=FONT_HEAD,
                     fg=C["bg"], bg=clr, padx=4).pack(side="left")
            tk.Label(rf, text=f"  {event}", font=FONT_MONO,
                     fg=C["accent"], bg=C["card"],
                     width=32, anchor="w").pack(side="left")
            tk.Label(rf, text=desc, font=FONT_BODY,
                     fg=C["text"], bg=C["card"]).pack(side="left")

        self._refresh_dashboard()
        return p

    def _refresh_dashboard(self):
        for title, (var, sql) in self._stat_vars.items():
            _, rows = run_query(sql)
            var.set(str(rows[0][0]) if rows else "?")

    # ─────────────────────────────────────────
    #  AVAILABLE CARS
    # ─────────────────────────────────────────
    def _panel_cars(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "AVAILABLE VEHICLES", bg=C["bg"]).pack(anchor="w", pady=(0, 8))
        tf, tree = make_tree(
            p, ["ID", "Reg No", "Model", "Category", "Fuel", "Status"],
            heights=18)
        tf.pack(fill="both", expand=True)
        def ref():
            c, r = run_query(
                "SELECT vehicle_id, registration_no, model, category, "
                "fuel_type, status FROM VEHICLE WHERE status='AVAILABLE' "
                "ORDER BY category, model")
            populate_tree(tree, c, r)
        btn(p, "🔄  Refresh", ref, width=16).pack(pady=8, anchor="w")
        ref()
        return p

    # ─────────────────────────────────────────
    #  CUSTOMERS & DOCUMENTS
    # ─────────────────────────────────────────
    def _panel_customers(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "CUSTOMERS & DOCUMENTS", bg=C["bg"]).pack(
            anchor="w", pady=(0, 8))
        top = tk.Frame(p, bg=C["bg"]); top.pack(fill="both", expand=True)
        top.columnconfigure(0, weight=2); top.columnconfigure(1, weight=3)

        lf = card_frame(top, padx=6, pady=6)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        label(lf, "CUSTOMERS", font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
        cf, ct = make_tree(lf, ["ID", "Name", "Email", "Membership"], heights=16)
        cf.pack(fill="both", expand=True, pady=4)

        rf = card_frame(top, padx=6, pady=6)
        rf.grid(row=0, column=1, sticky="nsew")
        label(rf, "DOCUMENTS  (click a customer row →)",
              font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
        df, dt = make_tree(
            rf, ["Doc ID", "Type", "Number", "Expiry", "Status"],
            heights=16)
        df.pack(fill="both", expand=True, pady=4)

        def load_cust():
            c, r = run_query("""
                SELECT cu.customer_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       cu.email, m.membership_type
                FROM   CUSTOMER cu
                LEFT JOIN MEMBERSHIP m ON cu.membership_id = m.membership_id
                ORDER  BY cu.customer_id""")
            populate_tree(ct, c, r)

        def on_sel(event):
            sel = ct.selection()
            if not sel: return
            cid = ct.item(sel[0])["values"][0]
            c, r = run_query("""
                SELECT document_id, document_type, document_number,
                       expiry_date, status
                FROM   DOCUMENT WHERE customer_id = %s""", (cid,))
            populate_tree(dt, c, r)
            for ch in dt.get_children():
                vals = dt.item(ch)["values"]
                st = vals[4] if len(vals) > 4 else ""
                if st == "VERIFIED":
                    dt.item(ch, tags=("ver",))
                elif st in ("EXPIRED", "REJECTED"):
                    dt.item(ch, tags=("bad",))
                else:
                    dt.item(ch, tags=("wrn",))
            dt.tag_configure("ver", foreground=C["accent2"])
            dt.tag_configure("bad", foreground=C["danger"])
            dt.tag_configure("wrn", foreground=C["warn"])

        ct.bind("<<TreeviewSelect>>", on_sel)
        btn(lf, "🔄  Refresh", load_cust, width=16).pack(pady=4, anchor="w")
        load_cust()
        return p

    # ─────────────────────────────────────────
    #  MAKE RESERVATION
    # ─────────────────────────────────────────
    def _panel_reservation(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "MAKE A RESERVATION", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
        label(p, "T1 blocks overlapping vehicle bookings  •  App blocks customer double-bookings.",
              fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=20, pady=20)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        label(fc, "RESERVATION FORM", font=FONT_HEAD,
              fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        db_hint_row(fc, row=1)
        e_cust = combo_row(fc, "Customer",   2, load_customers)
        e_veh  = combo_row(fc, "Vehicle",    3, load_vehicles_available)
        e_st   = form_row (fc, "Start Date", 4)
        hint_row(fc, "YYYY-MM-DD   e.g. 2026-05-01", 5)
        e_en   = form_row (fc, "End Date",   6)
        hint_row(fc, "YYYY-MM-DD   must be after Start Date", 7)
        log = log_box(fc, height=8)
        log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        def do():
            log_clear(log)
            cid = get_id(e_cust.get()); vid = get_id(e_veh.get())
            st_r = e_st.get().strip();   en_r = e_en.get().strip()
            st, en = validate_reservation(log, cid, vid, st_r, en_r)
            if st is None: return

            conflicts = vehicle_overlap_check(vid, st_r, en_r)
            if conflicts:
                log_write(log, "  ══" * 22, "err")
                log_write(log, "  ✗  VEHICLE BOOKING CONFLICT:", "err")
                for row in conflicts:
                    log_write(log, f"      Res #{row[0]}   {str(row[1])[:10]} → {str(row[2])[:10]}", "err")
                log_write(log, "  Choose different dates or a different vehicle.", "err")
                log_write(log, "  ══" * 22, "err")
                log_write(log, "  Forwarding to DB — Trigger 1 will also block it.", "warn")

            new_id = next_id("RESERVATION", "reservation_id", 6000)
            ok, msg = run_write("""
                INSERT INTO RESERVATION
                    (reservation_id, customer_id, vehicle_id,
                     start_date, end_date, status)
                VALUES (%s,%s,%s,%s,%s,'CONFIRMED')
            """, (new_id, cid, vid, st_r, en_r))

            if ok:
                log_write(log, "  ✔  Reservation confirmed!", "ok")
                log_write(log, f"     ID #{new_id}   {e_cust.get()[:30]}", "ok")
                log_write(log, f"     Period : {st}  →  {en}", "ok")
                ref_res()
            else:
                if "TRIGGER BLOCKED" in msg:
                    log_write(log, "  ══" * 22, "err")
                    log_write(log, "  TRIGGER 1 FIRED ✔ — DB-level overlap blocked!", "err")
                    log_write(log, f"  {msg}", "err")
                    log_write(log, "  ══" * 22, "err")
                else:
                    log_write(log, f"  ✗  {msg}", "err")

        btn(fc, "✓  Confirm Reservation", do,
            color=C["accent2"], width=26).grid(
            row=9, column=0, columnspan=2, pady=12)

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "EXISTING RESERVATIONS", font=FONT_HEAD,
              fg=C["muted"]).pack(anchor="w")
        rf, rt = make_tree(
            rc, ["Res ID", "Cust", "Veh", "Start", "End", "Status"],
            heights=18)
        rf.pack(fill="both", expand=True, pady=4)

        def ref_res():
            c, r = run_query("""
                SELECT reservation_id, customer_id, vehicle_id,
                       start_date, end_date, status
                FROM   RESERVATION ORDER BY reservation_id DESC""")
            populate_tree(rt, c, r)

        btn(rc, "🔄  Refresh", ref_res, width=14).pack(anchor="w")
        ref_res()
        return p

    # ─────────────────────────────────────────
    #  START RENTAL
    # ─────────────────────────────────────────
    def _panel_start(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "START A RENTAL  (PICKUP)", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
        label(p, "T2 checks documents  •  T3 flips vehicle → RENTED",
              fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=20, pady=20)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        label(fc, "PICKUP FORM", font=FONT_HEAD,
              fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,4))
        db_hint_row(fc, row=1)
        e_res    = combo_row(fc, "Reservation",   2, load_res_confirmed)
        e_branch = combo_row(fc, "Pickup Branch", 3, load_branches)
        e_dt     = form_row (fc, "Pickup DateTime", 4, w=25)
        hint_row(fc, "YYYY-MM-DD HH:MM:SS   e.g. 2026-04-01 10:00:00", 5)

        rv = {k: tk.StringVar(value="—") for k in ["cust","veh","from","to","rate"]}
        info_block_grid(fc, 6, "RESERVATION PREVIEW", [
            ("Customer    :", rv["cust"], C["text"]),
            ("Vehicle     :", rv["veh"],  C["accent"]),
            ("Booked From :", rv["from"], C["text"]),
            ("Booked To   :", rv["to"],   C["text"]),
            ("Eff. Rate   :", rv["rate"], C["accent2"]),
        ])

        vsv = {k: tk.StringVar(value="—") for k in ["vid", "bef", "aft"]}
        info_block_grid(fc, 7, "VEHICLE STATUS TRACKER  (T3)", [
            ("Vehicle # :", vsv["vid"], C["accent"]),
            ("BEFORE    :", vsv["bef"], C["warn"]),
            ("AFTER     :", vsv["aft"], C["accent2"]),
        ])

        log = log_box(fc, height=4)
        log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        def on_res_select(event=None):
            rid = get_id(e_res.get())
            for v in rv.values(): v.set("—")
            if not rid: return
            _, r = run_query("""
                SELECT CONCAT(c.first_name,' ',c.last_name),
                       v.model, v.category, v.vehicle_id,
                       res.start_date, res.end_date, m.discount_rate
                FROM   RESERVATION res
                JOIN   CUSTOMER c    ON res.customer_id  = c.customer_id
                JOIN   VEHICLE v     ON res.vehicle_id   = v.vehicle_id
                JOIN   MEMBERSHIP m  ON c.membership_id  = m.membership_id
                WHERE  res.reservation_id = %s
            """, (rid,))
            if not r: return
            cname, mdl, cat, vid, st, en, disc = r[0]
            rate = get_daily_rate(cat)
            eff  = rate * (1 - float(disc or 0) / 100)
            rv["cust"].set(cname)
            rv["veh"].set(f"#{vid} — {mdl} ({cat})")
            rv["from"].set(str(st)[:10])
            rv["to"].set(str(en)[:10])
            rv["rate"].set(f"${eff:.2f}/day  (${rate} − {disc}% discount)")

        e_res.bind("<<ComboboxSelected>>", on_res_select)

        def do():
            log_clear(log)
            for v in vsv.values(): v.set("—")
            res_id = get_id(e_res.get())
            bid    = get_id(e_branch.get())
            dt_raw = e_dt.get().strip()

            pdt = validate_rental_start(log, res_id, bid, dt_raw)
            if pdt is None: return

            _, r = run_query(
                "SELECT vehicle_id, status, start_date, end_date "
                "FROM RESERVATION WHERE reservation_id = %s", (res_id,))
            veh_id, res_st, res_start, res_end = r[0]

            if res_st != "CONFIRMED":
                log_write(log, f"  ✗  Reservation #{res_id} is '{res_st}'. Must be CONFIRMED.", "err")
                return

            _, vr = run_query(
                "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
            bef = vr[0][0] if vr else "?"
            vsv["vid"].set(str(veh_id)); vsv["bef"].set(bef)

            new_id = next_id("RENTAL", "rental_id", 7000, floor=7099)
            ok, msg = run_write("""
                INSERT INTO RENTAL
                    (rental_id, reservation_id, vehicle_id,
                     pickup_branch_id, pickup_date, status)
                VALUES (%s,%s,%s,%s,%s,'ACTIVE')
            """, (new_id, res_id, veh_id, bid, dt_raw))

            if ok:
                _, vr2 = run_query(
                    "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
                aft = vr2[0][0] if vr2 else "?"
                vsv["aft"].set(aft)
                log_write(log, f"  ✔  Rental #{new_id} started!", "ok")
                log_write(log, f"     Res #{res_id}  |  Pickup: {dt_raw}", "ok")
                log_write(log, f"     [T3 ✔]  Vehicle #{veh_id}: {bef} → {aft}", "ok")
                ref_start()
            else:
                if "TRIGGER BLOCKED" in msg:
                    log_write(log, "  ══" * 22, "err")
                    log_write(log, "  TRIGGER 2 FIRED ✔ — Customer docs invalid!", "err")
                    log_write(log, f"  {msg}", "err")
                    log_write(log, "  ══" * 22, "err")
                else:
                    log_write(log, f"  ✗  {msg}", "err")

        btn(fc, "▶  Start Rental", do,
            color=C["accent2"], width=24).grid(
            row=9, column=0, columnspan=2, pady=10)

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "CONFIRMED RESERVATIONS", font=FONT_HEAD,
              fg=C["muted"]).pack(anchor="w")
        rf, rt = make_tree(
            rc, ["Res ID", "Cust ID", "Veh ID", "Start", "End", "Status"],
            heights=18)
        rf.pack(fill="both", expand=True, pady=4)

        def ref_start():
            c, r = run_query("""
                SELECT reservation_id, customer_id, vehicle_id,
                       start_date, end_date, status
                FROM   RESERVATION WHERE status = 'CONFIRMED'
                ORDER  BY reservation_id""")
            populate_tree(rt, c, r)

        btn(rc, "🔄  Refresh", ref_start, width=14).pack(anchor="w")
        ref_start()
        return p

    # ─────────────────────────────────────────
    #  COMPLETE RENTAL
    # ─────────────────────────────────────────
    def _panel_end(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "COMPLETE A RENTAL  (RETURN)", bg=C["bg"]).pack(
            anchor="w", pady=(0, 4))
        label(p, "T4 flips vehicle → AVAILABLE",
              fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=20, pady=20)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        label(fc, "RETURN FORM", font=FONT_HEAD,
              fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,4))
        db_hint_row(fc, row=1)
        e_rid    = combo_row(fc, "Active Rental",   2, load_rentals_active)
        e_branch = combo_row(fc, "Return Branch",   3, load_branches)
        e_dt     = form_row (fc, "Return DateTime", 4)
        hint_row(fc, "YYYY-MM-DD HH:MM:SS   must be AFTER pickup time", 5)

        _ctx = {}
        pv = {k: tk.StringVar(value="—") for k in ["pu", "days", "rate", "est"]}
        prev_f = tk.Frame(fc, bg=C["border"], padx=12, pady=8)
        prev_f.grid(row=6, column=0, columnspan=2, sticky="ew", pady=6)
        tk.Label(prev_f, text="CHARGE PREVIEW  (live — updates as you type)",
                 font=FONT_HEAD, fg=C["warn"], bg=C["border"]).pack(
                 anchor="w", pady=(0, 4))
        grid_f = tk.Frame(prev_f, bg=C["border"]); grid_f.pack(fill="x")
        prev_fields = [
            ("Pickup Date :",  pv["pu"],   C["text"],    0, 0),
            ("Days Rented :",  pv["days"], C["text"],    1, 0),
            ("Daily Rate :",   pv["rate"], C["text"],    2, 0),
            ("Est. Total :",   pv["est"],  C["accent2"], 3, 0),
        ]
        for lbl_t, var, clr, pr, pc in prev_fields:
            tk.Label(grid_f, text=lbl_t, font=FONT_SMALL, fg=C["muted"],
                     bg=C["border"], width=14, anchor="w").grid(
                     row=pr, column=pc, sticky="w")
            tk.Label(grid_f, textvariable=var, font=FONT_MONO,
                     fg=clr, bg=C["border"]).grid(
                     row=pr, column=pc + 1, sticky="w", padx=(0, 16))

        rv = {k: tk.StringVar(value="—") for k in ["pu", "days", "total", "vs"]}
        info_block_grid(fc, 7, "COMPLETION RESULT  (T4)", [
            ("Pickup Date  :", rv["pu"],    C["text"]),
            ("Days Rented  :", rv["days"],  C["text"]),
            ("Total Charged:", rv["total"], C["accent2"]),
            ("Vehicle Now  :", rv["vs"],    C["accent2"]),
        ])
        log = log_box(fc, height=3)
        log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        def load_ctx(e=None):
            for v in pv.values(): v.set("—")
            _ctx.clear()
            rid = get_id(e_rid.get())
            if not rid: return
            _, r = run_query("""
                SELECT r.pickup_date, v.category, m.discount_rate
                FROM   RENTAL r
                JOIN   RESERVATION res ON r.reservation_id  = res.reservation_id
                JOIN   CUSTOMER c      ON res.customer_id   = c.customer_id
                JOIN   MEMBERSHIP m    ON c.membership_id   = m.membership_id
                JOIN   VEHICLE v       ON r.vehicle_id      = v.vehicle_id
                WHERE  r.rental_id = %s
            """, (rid,))
            if not r: return
            pu_raw, cat, disc = r[0]
            pdt = to_datetime(pu_raw)
            if pdt is None: return
            _ctx.update({"pdt": pdt, "cat": cat, "disc": disc})
            pv["pu"].set(str(pdt)[:19])
            _update_preview()

        def _update_preview(e=None):
            if not _ctx: return
            dt_r = e_dt.get().strip()
            if not dt_r: return
            rdt = parse_datetime(dt_r)
            if rdt is None or rdt <= _ctx["pdt"]: return
            ch = calc_charge(_ctx["cat"], _ctx["disc"], _ctx["pdt"], rdt)
            pv["days"].set(f"{ch['days']} day(s)")
            pv["rate"].set(f"${ch['eff']:.2f}/day")
            pv["est"].set(f"${ch['total']:.2f}")

        e_rid.bind("<<ComboboxSelected>>", load_ctx)
        e_dt.bind("<KeyRelease>", _update_preview)

        def do():
            log_clear(log)
            for v in rv.values(): v.set("—")
            rid    = get_id(e_rid.get())
            bid    = get_id(e_branch.get())
            dt_raw = e_dt.get().strip()

            ret_dt, veh_id, pickup_dt = validate_rental_end(log, rid, bid, dt_raw)
            if ret_dt is None: return

            ch = calc_charge(_ctx["cat"], _ctx["disc"], pickup_dt, ret_dt)
            total_amount = ch["total"]
            days_rented = ch["days"]

            rv["pu"].set(str(pickup_dt)[:19])
            rv["days"].set(f"{days_rented} day(s)")

            ok, msg = run_write("""
                UPDATE RENTAL SET status = 'COMPLETED',
                       return_branch_id = %s, return_date = %s, total_amount = %s
                WHERE  rental_id = %s
            """, (bid, dt_raw, total_amount, rid))

            if ok:
                _, tr = run_query(
                    "SELECT total_amount FROM RENTAL WHERE rental_id = %s", (rid,))
                total = tr[0][0] if tr else "?"
                _, vr = run_query(
                    "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
                vs = vr[0][0] if vr else "?"
                rv["total"].set(f"${total}")
                rv["vs"].set(vs)
                log_write(log, f"  ✔  Rental #{rid} completed! Total = ${total}", "ok")
                log_write(log, f"     [T4] Vehicle #{veh_id} → {vs}", "ok")
                log_write(log, "     → Go to Record Payment to settle the balance.", "info")
                ref_end()
            else:
                log_write(log, f"  ✗  {msg}", "err")

        btn(fc, "■  Complete Rental", do,
            color=C["danger"], width=24).grid(
            row=9, column=0, columnspan=2, pady=10)

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "ACTIVE RENTALS", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
        rf, rt = make_tree(
            rc, ["Rental ID", "Customer", "Model", "Pickup Date", "Status"],
            heights=11)
        rf.pack(fill="both", expand=True, pady=4)

        label(rc, "RECENTLY COMPLETED", font=FONT_HEAD, fg=C["muted"]).pack(
            anchor="w", pady=(6, 0))
        rf2, rt2 = make_tree(
            rc, ["Rental ID", "Customer", "Total $", "Return Date"], heights=8)
        rf2.pack(fill="both", expand=True, pady=4)

        def ref_end():
            c, r = run_query("""
                SELECT r.rental_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       v.model, r.pickup_date, r.status
                FROM   RENTAL r
                JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
                JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
                JOIN   VEHICLE v ON r.vehicle_id = v.vehicle_id
                WHERE  r.status = 'ACTIVE' ORDER BY r.pickup_date DESC""")
            populate_tree(rt, c, r)
            c2, r2 = run_query("""
                SELECT r.rental_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       r.total_amount, r.return_date
                FROM   RENTAL r
                JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
                JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
                WHERE  r.status = 'COMPLETED'
                ORDER  BY r.rental_id DESC LIMIT 8""")
            populate_tree(rt2, c2, r2)

        btn(rc, "🔄  Refresh", ref_end, width=14).pack(anchor="w")
        ref_end()
        return p

    # ─────────────────────────────────────────
    #  RECORD PAYMENT
    # ─────────────────────────────────────────
    def _panel_payment(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "RECORD A PAYMENT", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
        label(p, "Select a rental — balance is auto-calculated and pre-filled.",
              fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=20, pady=20)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        label(fc, "PAYMENT FORM", font=FONT_HEAD,
              fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,4))
        db_hint_row(fc, row=1)
        e_rid  = combo_row(fc, "Rental", 2, load_rentals_all)
        res_var = tk.StringVar(value="")

        bv = {k: tk.StringVar(value="—") for k in
              ["cust", "res", "total", "paid", "bal", "status"]}
        info_block_grid(fc, 3, "BALANCE SUMMARY", [
            ("Customer      :", bv["cust"],   C["text"]),
            ("Reservation   :", bv["res"],    C["accent"]),
            ("Total Charged :", bv["total"],  C["text"]),
            ("Already Paid  :", bv["paid"],   C["accent2"]),
            ("Balance Owing :", bv["bal"],    C["warn"]),
            ("Rental Status :", bv["status"], C["muted"]),
        ])

        e_amt  = form_row(fc, "Amount ($)", 4)
        hint_row(fc, "Pre-filled from outstanding balance — edit for partial", 5)
        e_type = static_combo_row(fc, "Payment Type", 6, PAYMENT_TYPES)
        log = log_box(fc, height=6)
        log.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        def on_sel(event=None):
            log_clear(log)
            for v in bv.values(): v.set("—")
            res_var.set(""); e_amt.delete(0, "end")
            rid = get_id(e_rid.get())
            if not rid: return
            _, r = run_query("""
                SELECT r.reservation_id, r.status,
                       CONCAT(c.first_name,' ',c.last_name)
                FROM   RENTAL r
                JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
                JOIN   CUSTOMER c ON res.customer_id = c.customer_id
                WHERE  r.rental_id = %s
            """, (rid,))
            if not r:
                log_write(log, f"  ✗  Rental #{rid} not found.", "err"); return
            res_id, rstatus, cname = r[0]
            total, paid, bal = get_balance(rid)
            bv["cust"].set(cname); bv["res"].set(f"#{res_id}")
            bv["total"].set(f"${total:.2f}" if total > 0 else "— complete rental first")
            bv["paid"].set(f"${paid:.2f}"); bv["bal"].set(f"${bal:.2f}")
            bv["status"].set(rstatus); res_var.set(str(res_id))

            if rstatus != "COMPLETED":
                e_amt.insert(0, "0.00")
                log_write(log, f"  ⚠  Rental is still {rstatus}. Complete it first for exact total.", "warn")
            elif bal <= 0.005:
                e_amt.insert(0, "0.00")
                log_write(log, "  ✔  This rental is already fully paid.", "ok")
            else:
                e_amt.insert(0, f"{bal:.2f}")
                if paid > 0:
                    log_write(log, f"  ⚠  ${paid:.2f} already paid. Remaining balance: ${bal:.2f}", "warn")
                else:
                    log_write(log, f"  ✔  Amount pre-filled: ${bal:.2f}", "ok")

        e_rid.bind("<<ComboboxSelected>>", on_sel)

        def do():
            log_clear(log)
            rid   = get_id(e_rid.get())
            resid = res_var.get().strip()
            amt   = e_amt.get().strip()
            ptype = e_type.get().strip()
            if not rid:   log_write(log, "  ✗  Please select a Rental.", "err");         return
            if not resid: log_write(log, "  ✗  Select a rental first (reservation auto-fills).", "err"); return
            if not amt:   log_write(log, "  ✗  Amount is required.", "err");              return
            if not ptype: log_write(log, "  ✗  Please select a Payment Type.", "err");   return
            try:
                amount = float(amt)
            except ValueError:
                log_write(log, f"  ✗  '{amt}' is not a valid number.", "err"); return
            if amount <= 0:
                log_write(log, "  ✗  Amount must be greater than $0.00.", "err"); return

            total, paid, bal = get_balance(rid)
            if total > 0 and amount > bal + 0.01:
                log_write(log, f"  ⚠  Paying ${amount:.2f} but balance is only ${bal:.2f}  (overpayment).", "warn")

            new_id = next_id("PAYMENT", "payment_id", 8000)
            ok, msg = run_write("""
                INSERT INTO PAYMENT
                    (payment_id, rental_id, reservation_id,
                     amount, payment_type, status)
                VALUES (%s,%s,%s,%s,%s,'COMPLETED')
            """, (new_id, rid, resid, amount, ptype))

            if ok:
                t2, p2, b2 = get_balance(rid)
                log_write(log, f"  ✔  Payment #{new_id} recorded!", "ok")
                log_write(log, f"     ${amount:,.2f} via {ptype}", "ok")
                log_write(log, f"     Balance: ${b2:.2f}",
                    "ok" if b2 <= 0.005 else "warn")
                if b2 <= 0.005:
                    log_write(log, "     ✔  FULLY PAID", "ok")
                ref_pay(); on_sel()
            else:
                log_write(log, f"  ✗  {msg}", "err")

        btn(fc, "$  Record Payment", do,
            color=C["accent2"], width=24).grid(
            row=8, column=0, columnspan=2, pady=10)

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "RECENT PAYMENTS", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
        rf, rt = make_tree(
            rc, ["Pay ID", "Rental", "Customer", "Amount", "Type", "Status"],
            heights=10)
        rf.pack(fill="both", expand=True, pady=4)

        label(rc, "COMPLETED RENTALS — BALANCE VIEW",
              font=FONT_HEAD, fg=C["muted"]).pack(anchor="w", pady=(6, 0))
        bf, bt = make_tree(
            rc, ["Rental", "Customer", "Total", "Paid", "Balance"],
            heights=9)
        bf.pack(fill="both", expand=True, pady=4)

        def ref_pay():
            c, r = run_query("""
                SELECT p.payment_id, p.rental_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       p.amount, p.payment_type, p.status
                FROM   PAYMENT p
                JOIN   RENTAL r2    ON p.rental_id        = r2.rental_id
                JOIN   RESERVATION s ON r2.reservation_id = s.reservation_id
                JOIN   CUSTOMER cu  ON s.customer_id      = cu.customer_id
                ORDER  BY p.payment_id DESC""")
            populate_tree(rt, c, r)
            _, r2 = run_query("""
                SELECT r.rental_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       r.total_amount,
                       COALESCE(SUM(p.amount),0),
                       GREATEST(r.total_amount - COALESCE(SUM(p.amount),0), 0)
                FROM   RENTAL r
                JOIN   RESERVATION s ON r.reservation_id  = s.reservation_id
                JOIN   CUSTOMER cu   ON s.customer_id     = cu.customer_id
                LEFT JOIN PAYMENT p  ON r.rental_id = p.rental_id
                                     AND p.status = 'COMPLETED'
                WHERE  r.status = 'COMPLETED'
                GROUP  BY r.rental_id, cu.first_name, cu.last_name, r.total_amount
                ORDER  BY r.rental_id DESC LIMIT 15""")
            populate_tree(bt, [], r2)
            for ch in bt.get_children():
                vals = bt.item(ch)["values"]
                try:
                    b = float(str(vals[4]).replace("NULL", "0"))
                    bt.item(ch, tags=("paid",) if b <= 0.005 else ("owing",))
                except Exception:
                    pass
            bt.tag_configure("paid",  foreground=C["accent2"])
            bt.tag_configure("owing", foreground=C["warn"])

        btn(rc, "🔄  Refresh", ref_pay, width=14).pack(anchor="w")
        ref_pay()
        return p

    # ─────────────────────────────────────────
    #  ACTIVE RENTALS
    # ─────────────────────────────────────────
    def _panel_active(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "ACTIVE RENTALS", bg=C["bg"]).pack(anchor="w", pady=(0, 8))
        tf, tree = make_tree(
            p, ["Rental ID", "Customer", "Model", "Reg No",
                "Pickup Branch", "Pickup Date", "Status"],
            heights=20)
        tf.pack(fill="both", expand=True)
        def ref():
            c, r = run_query("""
                SELECT r.rental_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       v.model, v.registration_no,
                       b.branch_name, r.pickup_date, r.status
                FROM   RENTAL r
                JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
                JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
                JOIN   VEHICLE v ON r.vehicle_id = v.vehicle_id
                JOIN   BRANCH b ON r.pickup_branch_id = b.branch_id
                WHERE  r.status = 'ACTIVE' ORDER BY r.pickup_date DESC""")
            populate_tree(tree, c, r)
        btn(p, "🔄  Refresh", ref, width=16).pack(pady=8, anchor="w")
        ref()
        return p

    # ─────────────────────────────────────────
    #  REVENUE REPORT
    # ─────────────────────────────────────────
    def _panel_revenue(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "GLOBAL REVENUE REPORT", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
        label(p, "Revenue grouped by country of pickup branch",
              fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))
        top = tk.Frame(p, bg=C["bg"]); top.pack(fill="both", expand=True)
        top.columnconfigure(0, weight=1); top.columnconfigure(1, weight=1)

        lf = card_frame(top, padx=8, pady=8)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        label(lf, "BY COUNTRY", font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
        cf, ct = make_tree(lf, ["Country", "Transactions", "Total Revenue ($)"], heights=12)
        cf.pack(fill="both", expand=True, pady=4)

        rf = card_frame(top, padx=8, pady=8)
        rf.grid(row=0, column=1, sticky="nsew")
        label(rf, "BY MEMBERSHIP TIER", font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
        mf, mt = make_tree(rf, ["Tier", "Total Revenue ($)"], heights=12)
        mf.pack(fill="both", expand=True, pady=4)

        def ref():
            c, r = run_query("""
                SELECT co.country_name, COUNT(p.payment_id),
                       COALESCE(SUM(p.amount), 0)
                FROM   PAYMENT p
                JOIN   RENTAL r2 ON p.rental_id = r2.rental_id
                JOIN   BRANCH b  ON r2.pickup_branch_id = b.branch_id
                JOIN   CITY ci   ON b.city_id = ci.city_id
                JOIN   COUNTRY co ON ci.country_code = co.country_code
                GROUP  BY co.country_name ORDER BY 3 DESC""")
            populate_tree(ct, c, r)
            c2, r2 = run_query("""
                SELECT m.membership_type,
                       COALESCE(SUM(p.amount), 0) AS revenue
                FROM   PAYMENT p
                JOIN   RESERVATION res ON p.reservation_id = res.reservation_id
                JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
                JOIN   MEMBERSHIP m ON cu.membership_id = m.membership_id
                GROUP  BY m.membership_type ORDER BY revenue DESC""")
            populate_tree(mt, c2, r2)

        btn(p, "🔄  Refresh", ref, width=16).pack(pady=8, anchor="w")
        ref()
        return p

    # ─────────────────────────────────────────
    #  TRIGGER DEMO PANEL
    # ─────────────────────────────────────────
    def _panel_triggers(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "⚡ TRIGGER DEMONSTRATION PANEL",
                fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 2))
        label(p, "Live before/after proof for all trigger events — TA demo ready",
              fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        s = ttk.Style()
        s.configure("Trig.TNotebook", background=C["bg"], tabmargins=[2, 4, 2, 0])
        s.configure("Trig.TNotebook.Tab",
                    background=C["card"], foreground=C["text"],
                    font=FONT_HEAD, padding=[14, 6])
        s.map("Trig.TNotebook.Tab",
              background=[("selected", C["warn"])],
              foreground=[("selected", C["bg"])])

        nb = ttk.Notebook(p, style="Trig.TNotebook")
        nb.pack(fill="both", expand=True)
        nb.add(self._t1(nb), text=" T1 — Overlap Block ")
        nb.add(self._t2(nb), text=" T2 — Doc Check ")
        nb.add(self._t3(nb), text=" T3 — Status -> RENTED ")
        nb.add(self._t4(nb), text=" T4 — Status -> AVAILABLE ")
        return p

    def _t1(self, parent):
        f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

        hf = card_frame(f, padx=14, pady=10)
        hf.pack(fill="x", pady=(0, 10))
        tk.Label(hf, text="TRIGGER 1  —  BEFORE INSERT ON RESERVATION",
                 font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="LOGIC: Overlap is checked purely on DATES for the same vehicle — "
                      "regardless of the vehicle's current status (AVAILABLE / RENTED). "
                      "If any CONFIRMED reservation for that vehicle has dates that "
                      "overlap the requested period, the INSERT is blocked.",
                 font=FONT_SMALL, fg=C["text"], bg=C["card"],
                 wraplength=700, justify="left").pack(anchor="w", pady=(4, 2))
        tk.Label(hf,
                 text="TO FAIL ▶  Pick any vehicle, enter dates that overlap an existing booking (see right table).",
                 font=FONT_SMALL, fg=C["danger"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="TO PASS ▶  Enter dates with no overlap for the chosen vehicle.",
                 font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="★ NOTE: Customer double-booking (same customer, overlapping dates) is also blocked at the app level.",
                 font=FONT_SMALL, fg=C["accent"], bg=C["card"]).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=16, pady=16)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        db_hint_row(fc, row=0)
        e_cust  = combo_row(fc, "Customer",   1, load_customers)
        e_veh   = combo_row(fc, "Vehicle",    2, load_vehicles_all_no_status)
        e_start = form_row (fc, "Start Date", 3)
        hint_row(fc, "YYYY-MM-DD", 4)
        e_end   = form_row (fc, "End Date",   5)
        hint_row(fc, "YYYY-MM-DD   must be after Start Date", 6)
        log = log_box(fc, height=11)
        log.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        def do():
            log_clear(log)
            cid   = get_id(e_cust.get()); vid = get_id(e_veh.get())
            st_r  = e_start.get().strip();   en_r = e_end.get().strip()
            st, en = validate_reservation(log, cid, vid, st_r, en_r)
            if st is None: return

            conflicts = vehicle_overlap_check(vid, st_r, en_r)
            if conflicts:
                log_write(log, f"  Pre-check: {len(conflicts)} vehicle conflict(s) for Vehicle #{vid}:", "warn")
                for row in conflicts:
                    log_write(log,
                        f"    Res #{row[0]}   "
                        f"{str(row[1])[:10]} → {str(row[2])[:10]}", "warn")
                log_write(log, "  Sending to DB — Trigger 1 should block…", "warn")
            else:
                log_write(log, "  Pre-check: No client-side conflict found. Sending to DB…", "info")

            new_id = next_id("RESERVATION", "reservation_id", 6000)
            log_write(log, f"  Attempting Reservation #{new_id}  ({st_r} → {en_r})…", "info")

            ok, msg = run_write("""
                INSERT INTO RESERVATION
                    (reservation_id, customer_id, vehicle_id,
                     start_date, end_date, status)
                VALUES (%s,%s,%s,%s,%s,'CONFIRMED')
            """, (new_id, cid, vid, st_r, en_r))

            if ok:
                log_write(log, "", "info")
                log_write(log, "  ✔  PASS — No overlap. Reservation inserted.", "ok")
                log_write(log, f"     Reservation #{new_id} confirmed.", "ok")
            else:
                if "TRIGGER BLOCKED" in msg:
                    log_write(log, "", "err")
                    log_write(log, "  ══" * 22, "err")
                    log_write(log, "  TRIGGER 1 FIRED ✔", "err")
                    log_write(log, "  Overlapping reservation BLOCKED at DB level!", "err")
                    log_write(log, f"  {msg}", "err")
                    log_write(log, "  ══" * 22, "err")
                else:
                    log_write(log, f"  ✗  DB Error: {msg}", "err")
            ref_t1()

        btn(fc, "⚡ Run Trigger 1 Test", do,
            color=C["warn"], width=24).grid(
            row=8, column=0, columnspan=2, pady=10)

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "EXISTING RESERVATIONS  (check dates before testing)",
              font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
        label(rc,
              "Look up the vehicle you choose and find dates that overlap → T1 will block.",
              font=FONT_SMALL, fg=C["muted"]).pack(anchor="w", pady=(0, 4))
        rf, rt = make_tree(
            rc, ["Res ID", "Cust", "Veh", "Start", "End", "Status"],
            heights=20)
        rf.pack(fill="both", expand=True, pady=4)

        def ref_t1():
            c, r = run_query("""
                SELECT reservation_id, customer_id, vehicle_id,
                       start_date, end_date, status
                FROM   RESERVATION ORDER BY vehicle_id, start_date""")
            populate_tree(rt, c, r)

        btn(rc, "🔄 Refresh", ref_t1, width=12).pack(anchor="w")
        ref_t1()
        return f

    def _t2(self, parent):
        f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

        hf = card_frame(f, padx=14, pady=10)
        hf.pack(fill="x", pady=(0, 10))
        tk.Label(hf, text="TRIGGER 2  —  BEFORE INSERT ON RENTAL",
                 font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="LOGIC: The trigger checks whether the customer has AT LEAST ONE "
                      "document with status='VERIFIED' AND expiry_date >= today. "
                      "Even one expired/invalid document does NOT cause a block — "
                      "only having ZERO valid documents causes the INSERT to be rejected.",
                 font=FONT_SMALL, fg=C["text"], bg=C["card"],
                 wraplength=700, justify="left").pack(anchor="w", pady=(4, 2))
        tk.Label(hf,
                 text="TO FAIL ▶  Customers 1003 (EXPIRED) | 1006 (PENDING) | 1007 (no doc)",
                 font=FONT_SMALL, fg=C["danger"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="TO PASS ▶  Customers 1001, 1002, 1004, 1005, 1008, 1009",
                 font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w")

        body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=16, pady=16)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        db_hint_row(fc, row=0)
        e_res    = combo_row(fc, "Reservation",  1, load_res_confirmed)
        e_branch = combo_row(fc, "Pickup Branch", 2, load_branches)
        e_dt     = form_row (fc, "Pickup DateTime", 3)
        hint_row(fc, "YYYY-MM-DD HH:MM:SS   e.g. 2026-04-01 10:00:00", 4)

        veh_var = tk.StringVar(value="— select a Reservation —")
        tk.Label(fc, text="Vehicle (auto):", font=FONT_SMALL,
                 fg=C["muted"], bg=C["card"]).grid(
                 row=5, column=0, sticky="w", pady=4)
        tk.Label(fc, textvariable=veh_var, font=FONT_HEAD,
                 fg=C["accent"], bg=C["card"]).grid(
                 row=5, column=1, sticky="w", pady=4)

        log = log_box(fc, height=14)
        log.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        def do():
            log_clear(log); veh_var.set("…")
            res_id = get_id(e_res.get())
            bid    = get_id(e_branch.get())
            dt_raw = e_dt.get().strip()

            pdt = validate_rental_start(log, res_id, bid, dt_raw)
            if pdt is None: return

            _, r = run_query(
                "SELECT vehicle_id, status, customer_id, start_date, end_date "
                "FROM RESERVATION WHERE reservation_id = %s", (res_id,))
            veh_id, rs, cid, res_st, res_en = r[0]
            veh_var.set(f"#{veh_id}")

            if rs != "CONFIRMED":
                log_write(log, f"  ✗  Reservation is '{rs}'. Must be CONFIRMED.", "err")
                return

            has_valid, docs = customer_doc_status(cid)
            log_write(log, f"  Customer #{cid} — Document check:", "heading")
            log_write(log, "  " + "─" * 55, "info")
            if docs:
                for d_type, d_status, d_exp in docs:
                    is_valid = (d_status == "VERIFIED")
                    tag  = "ok" if is_valid else "err"
                    mark = "✔ VALID" if is_valid else "✗ INVALID"
                    log_write(log,
                        f"    {d_type:<28}  {d_status:<12}  "
                        f"exp:{str(d_exp)[:10]}   [{mark}]", tag)
            else:
                log_write(log, "    (no documents on file)  → WILL BE BLOCKED", "err")
            log_write(log, "  " + "─" * 55, "info")
            if has_valid:
                log_write(log,
                    "  ✔ Pre-check: At least one VERIFIED, unexpired doc found. "
                    "Expecting PASS.", "ok")
            else:
                log_write(log,
                    "  ✗ Pre-check: NO valid document found. "
                    "Trigger 2 WILL fire.", "warn")

            new_id = next_id("RENTAL", "rental_id", 7000, floor=7099)
            log_write(log, f"\n  Sending INSERT for Rental #{new_id}…", "info")

            ok, msg = run_write("""
                INSERT INTO RENTAL
                    (rental_id, reservation_id, vehicle_id,
                     pickup_branch_id, pickup_date, status)
                VALUES (%s,%s,%s,%s,%s,'ACTIVE')
            """, (new_id, res_id, veh_id, bid, dt_raw))

            if ok:
                _, vr = run_query(
                    "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
                log_write(log, "  ✔  PASS — Rental started. Valid document confirmed.", "ok")
                log_write(log, f"     Rental #{new_id} is now ACTIVE.", "ok")
            else:
                if "TRIGGER BLOCKED" in msg:
                    log_write(log, "  ══" * 22, "err")
                    log_write(log, "  TRIGGER 2 FIRED ✔", "err")
                    log_write(log, "  Rental BLOCKED — no valid document!", "err")
                    log_write(log, f"  {msg}", "err")
                    log_write(log, "  ══" * 22, "err")
                else:
                    log_write(log, f"  ✗  {msg}", "err")

        btn(fc, "⚡ Run Trigger 2 Test", do,
            color=C["warn"], width=24).grid(
            row=7, column=0, columnspan=2, pady=10)

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "ALL CUSTOMER DOCUMENTS  (reference)",
              font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
        label(rc,
              "Green = VERIFIED & non-expired (counts as valid)   "
              "Red = expired / rejected / pending",
              font=FONT_SMALL, fg=C["muted"]).pack(anchor="w", pady=(0, 4))
        df, dt2 = make_tree(
            rc, ["Cust ID", "Name", "Doc Type", "Status", "Expiry"],
            heights=20)
        df.pack(fill="both", expand=True, pady=4)

        def ref_t2():
            c, r = run_query("""
                SELECT cu.customer_id,
                       CONCAT(cu.first_name,' ',cu.last_name),
                       d.document_type, d.status, d.expiry_date
                FROM   CUSTOMER cu
                LEFT JOIN DOCUMENT d ON cu.customer_id = d.customer_id
                ORDER  BY cu.customer_id""")
            populate_tree(dt2, c, r)
            for ch in dt2.get_children():
                vals = dt2.item(ch)["values"]
                st = vals[3] if len(vals) > 3 else ""
                if st == "VERIFIED":
                    dt2.item(ch, tags=("ok",))
                elif st in ("EXPIRED", "REJECTED"):
                    dt2.item(ch, tags=("bad",))
                else:
                    dt2.item(ch, tags=("wrn",))
            dt2.tag_configure("ok",  foreground=C["accent2"])
            dt2.tag_configure("bad", foreground=C["danger"])
            dt2.tag_configure("wrn", foreground=C["warn"])

        btn(rc, "🔄 Refresh", ref_t2, width=12).pack(anchor="w")
        ref_t2()
        return f

    def _t3(self, parent):
        outer = tk.Frame(parent, bg=C["bg"])

        hf = tk.Frame(outer, bg=C["card"], padx=14, pady=10)
        hf.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(hf, text="TRIGGER 3  —  AFTER INSERT ON RENTAL",
                 font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="LOGIC: Automatically updates vehicle.status to 'RENTED' when a new rental starts.",
                 font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w", pady=(4, 0))
        tk.Label(hf,
                 text="TO TEST ▶  Fill the Pickup form below and click Start Rental. Watch the tracker update.",
                 font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(outer, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        left_outer = tk.Frame(body, bg=C["bg"])
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left = make_scrollable(left_outer, bg=C["bg"])

        tracker = tk.Frame(left, bg=C["border"], padx=14, pady=12)
        tracker.pack(fill="x", pady=(0, 10))
        tk.Label(tracker, text="◉  VEHICLE STATUS TRACKER",
                 font=FONT_HEAD, fg=C["warn"], bg=C["border"]).pack(anchor="w")

        vl_var  = tk.StringVar(value="Vehicle : —")
        bef_var = tk.StringVar(value="BEFORE  : —")
        aft_var = tk.StringVar(value="AFTER   : —")
        for var, fg_clr in [(vl_var, C["accent"]), (bef_var, C["warn"]), (aft_var, C["accent2"])]:
            tk.Label(tracker, textvariable=var, font=("Courier New", 12, "bold"),
                     fg=fg_clr, bg=C["border"]).pack(anchor="w", pady=2)

        fa = tk.Frame(left, bg=C["card"], padx=14, pady=12)
        fa.pack(fill="x", pady=(4, 6))
        tk.Label(fa, text="▶  TRIGGER 3 — Start Rental (Pickup)",
                 font=FONT_HEAD, fg=C["accent"], bg=C["card"]).grid(
                 row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        db_hint_row(fa, row=1)
        e3_res    = combo_row(fa, "Reservation",   2, load_res_confirmed)
        e3_branch = combo_row(fa, "Pickup Branch", 3, load_branches)
        e3_dt     = form_row (fa, "Pickup DateTime", 4)
        hint_row(fa, "YYYY-MM-DD HH:MM:SS", 5)
        log3 = log_box(fa, height=8)
        log3.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        def do_3():
            log_clear(log3); bef_var.set("BEFORE  : —"); aft_var.set("AFTER   : —"); vl_var.set("Vehicle : —")
            res_id = get_id(e3_res.get()); bid = get_id(e3_branch.get()); dt_raw = e3_dt.get().strip()

            pdt = validate_rental_start(log3, res_id, bid, dt_raw)
            if pdt is None: return

            _, r = run_query("SELECT vehicle_id, status FROM RESERVATION WHERE reservation_id = %s", (res_id,))
            veh_id, rs = r[0]

            if rs != "CONFIRMED":
                log_write(log3, f"  ✗  Reservation is '{rs}'. Must be CONFIRMED.", "err")
                return

            _, vr = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
            bef = vr[0][0] if vr else "?"
            vl_var.set(f"Vehicle : #{veh_id}"); bef_var.set(f"BEFORE  : {bef}")

            new_id = next_id("RENTAL", "rental_id", 7000, floor=7099)
            ok, msg = run_write("""
                INSERT INTO RENTAL (rental_id, reservation_id, vehicle_id, pickup_branch_id, pickup_date, status)
                VALUES (%s,%s,%s,%s,%s,'ACTIVE')
            """, (new_id, res_id, veh_id, bid, dt_raw))

            if ok:
                _, vr2 = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
                aft = vr2[0][0] if vr2 else "?"
                aft_var.set(f"AFTER   : {aft}")
                log_write(log3, f"  ✔  [T3 ✔]  Vehicle #{veh_id}:  {bef}  →  {aft}", "ok")
                log_write(log3, f"     Rental #{new_id} is now ACTIVE.", "ok")
                
                # AUTO-REFRESH LOGIC
                e3_res.set('')
                e3_dt.delete(0, 'end')
                e3_res['values'] = load_res_confirmed()
                ref_t3()
            else:
                log_write(log3, f"  ✗  {msg}", "err")

        btn(fa, "▶  Test Trigger 3", do_3, color=C["accent"], width=24).grid(row=7, column=0, columnspan=2, pady=(10, 2))

        # ── Right column: reference tables ───────────────────────────────
        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")

        # Header frame to hold Title (Left) and Refresh Button (Right)
        header_f = tk.Frame(rc, bg=C["card"])
        header_f.pack(fill="x", pady=(0, 4))
        
        label(header_f, "VEHICLE STATUS  (live)", font=FONT_HEAD, fg=C["muted"]).pack(side="left")

        def ref_t3():
            c, r = run_query("SELECT vehicle_id, model, category, status FROM VEHICLE ORDER BY vehicle_id")
            populate_tree(vt, c, r)
            for ch in vt.get_children():
                st = vt.item(ch)["values"][3]
                vt.item(ch, tags=("rented",) if st == "RENTED" else ("avail",))
            vt.tag_configure("rented", foreground=C["danger"])
            vt.tag_configure("avail",  foreground=C["accent2"])

        btn(header_f, "🔄 Refresh", ref_t3, width=12).pack(side="right")

        vf, vt = make_tree(rc, ["ID", "Model", "Category", "Status"], heights=20)
        vf.pack(fill="both", expand=True)

        ref_t3()
        return outer

    def _t4(self, parent):
        outer = tk.Frame(parent, bg=C["bg"])

        hf = tk.Frame(outer, bg=C["card"], padx=14, pady=10)
        hf.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(hf, text="TRIGGER 4  —  AFTER UPDATE ON RENTAL (status → 'COMPLETED')",
                 font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf,
                 text="LOGIC: Automatically updates vehicle.status to 'AVAILABLE' when a rental is completed.",
                 font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w", pady=(4, 0))
        tk.Label(hf,
                 text="TO TEST ▶  Select an active rental, enter the return datetime, and click Complete Rental.",
                 font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(outer, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        left_outer = tk.Frame(body, bg=C["bg"])
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left = make_scrollable(left_outer, bg=C["bg"])

        tracker = tk.Frame(left, bg=C["border"], padx=14, pady=12)
        tracker.pack(fill="x", pady=(0, 10))
        tk.Label(tracker, text="◉  VEHICLE STATUS TRACKER", font=FONT_HEAD, fg=C["warn"], bg=C["border"]).pack(anchor="w")

        vl_var  = tk.StringVar(value="Vehicle : —")
        bef_var = tk.StringVar(value="BEFORE  : —")
        aft_var = tk.StringVar(value="AFTER   : —")
        for var, fg_clr in [(vl_var, C["accent"]), (bef_var, C["warn"]), (aft_var, C["accent2"])]:
            tk.Label(tracker, textvariable=var, font=("Courier New", 12, "bold"), fg=fg_clr, bg=C["border"]).pack(anchor="w", pady=2)

        fb = tk.Frame(left, bg=C["card"], padx=14, pady=12)
        fb.pack(fill="x", pady=(4, 6))
        tk.Label(fb, text="■  TRIGGER 4 — Complete Rental (Return)", font=FONT_HEAD, fg=C["accent"], bg=C["card"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        db_hint_row(fb, row=1)
        e4_rid    = combo_row(fb, "Active Rental",   2, load_rentals_active)
        e4_branch = combo_row(fb, "Return Branch",   3, load_branches)
        e4_dt     = form_row (fb, "Return DateTime", 4)
        hint_row(fb, "YYYY-MM-DD HH:MM:SS", 5)
        log4 = log_box(fb, height=8)
        log4.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        _ctx = {}

        def load_ctx(e=None):
            _ctx.clear()
            rid = get_id(e4_rid.get())
            if not rid: return
            _, r = run_query("""
                SELECT r.pickup_date, v.category, m.discount_rate
                FROM   RENTAL r
                JOIN   RESERVATION res ON r.reservation_id  = res.reservation_id
                JOIN   CUSTOMER c      ON res.customer_id   = c.customer_id
                JOIN   MEMBERSHIP m    ON c.membership_id   = m.membership_id
                JOIN   VEHICLE v       ON r.vehicle_id      = v.vehicle_id
                WHERE  r.rental_id = %s
            """, (rid,))
            if not r: return
            pdt = to_datetime(r[0][0])
            _ctx.update({"pdt": pdt, "cat": r[0][1], "disc": r[0][2]})

        e4_rid.bind("<<ComboboxSelected>>", load_ctx)

        def do_4():
            log_clear(log4); bef_var.set("BEFORE  : —"); aft_var.set("AFTER   : —"); vl_var.set("Vehicle : —")
            rid = get_id(e4_rid.get()); bid = get_id(e4_branch.get()); dt_raw = e4_dt.get().strip()

            ret_dt, veh_id, pickup_dt = validate_rental_end(log4, rid, bid, dt_raw)
            if ret_dt is None: return

            _, vr = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
            bef = vr[0][0] if vr else "?"
            bef_var.set(f"BEFORE  : {bef}"); vl_var.set(f"Vehicle : #{veh_id}")

            ch = calc_charge(_ctx["cat"], _ctx["disc"], pickup_dt, ret_dt)
            total_amt = ch["total"]

            ok, msg = run_write("""
                UPDATE RENTAL SET status = 'COMPLETED',
                       return_branch_id = %s, return_date = %s, total_amount = %s
                WHERE  rental_id = %s
            """, (bid, dt_raw, total_amt, rid))

            if ok:
                _, vr2 = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
                aft = vr2[0][0] if vr2 else "?"
                aft_var.set(f"AFTER   : {aft}")
                log_write(log4, f"  ✔  [T4 ✔]  Vehicle #{veh_id}:  {bef}  →  {aft}", "ok")
                log_write(log4, f"     Rental #{rid} is now COMPLETED. (Total: ${total_amt:.2f})", "ok")
                
                # AUTO-REFRESH LOGIC
                e4_rid.set('')
                e4_dt.delete(0, 'end')
                e4_rid['values'] = load_rentals_active()
                ref_t4()
            else:
                log_write(log4, f"  ✗  {msg}", "err")

        btn(fb, "■  Test Trigger 4", do_4, color=C["danger"], width=24).grid(row=7, column=0, columnspan=2, pady=(10, 2))

        # ── Right column: reference tables ───────────────────────────────
        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")

        # Header frame to hold Title (Left) and Refresh Button (Right)
        header_f = tk.Frame(rc, bg=C["card"])
        header_f.pack(fill="x", pady=(0, 4))
        
        label(header_f, "VEHICLE STATUS  (live)", font=FONT_HEAD, fg=C["muted"]).pack(side="left")

        def ref_t4():
            c, r = run_query("SELECT vehicle_id, model, category, status FROM VEHICLE ORDER BY vehicle_id")
            populate_tree(vt, c, r)
            for ch in vt.get_children():
                st = vt.item(ch)["values"][3]
                vt.item(ch, tags=("rented",) if st == "RENTED" else ("avail",))
            vt.tag_configure("rented", foreground=C["danger"])
            vt.tag_configure("avail",  foreground=C["accent2"])

        btn(header_f, "🔄 Refresh", ref_t4, width=12).pack(side="right")

        vf, vt = make_tree(rc, ["ID", "Model", "Category", "Status"], heights=20)
        vf.pack(fill="both", expand=True)

        ref_t4()
        return outer

    # ─────────────────────────────────────────
    #  TASK 6: TRANSACTIONS DEMO PANEL
    # ─────────────────────────────────────────
    def _panel_transactions(self):
        p = tk.Frame(self.container, bg=C["bg"])
        heading(p, "🔄 TASK 6: TRANSACTIONS DEMO",
                fg=C["accent2"], bg=C["bg"]).pack(anchor="w", pady=(0, 2))
        label(p, "Demonstrate Atomicity (Commit/Rollback) and Isolation (Concurrency & Locks)",
              fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

        s = ttk.Style()
        s.configure("Tx.TNotebook", background=C["bg"], tabmargins=[2, 4, 2, 0])
        s.configure("Tx.TNotebook.Tab",
                    background=C["card"], foreground=C["text"],
                    font=FONT_HEAD, padding=[14, 6])
        s.map("Tx.TNotebook.Tab",
              background=[("selected", C["accent2"])],
              foreground=[("selected", C["bg"])])

        nb = ttk.Notebook(p, style="Tx.TNotebook")
        nb.pack(fill="both", expand=True)
        nb.add(self._tx_atomicity(nb), text=" Part A: Atomicity (Commit/Rollback) ")
        nb.add(self._tx_isolation(nb), text=" Part B: Isolation (Concurrency Conflict) ")
        return p

    def _tx_atomicity(self, parent):
        f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

        hf = card_frame(f, padx=14, pady=10)
        hf.pack(fill="x", pady=(0, 10))
        tk.Label(hf, text="SCENARIO: A customer makes a Reservation AND pays a Deposit in a single Transaction.",
                 font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf, text="SUCCESS: The DB successfully saves BOTH the Reservation and the Payment (COMMIT).\n"
                          "FAILURE: The Payment fails midway. The DB reverses the Reservation to prevent orphaned data (ROLLBACK).",
                 font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

        fc = card_frame(body, padx=16, pady=16)
        fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        e_cust = combo_row(fc, "Customer", 0, load_customers)
        e_veh  = combo_row(fc, "Vehicle", 1, load_vehicles_available)
        e_st   = form_row(fc, "Start Date", 2); e_st.insert(0, "2026-12-01")
        e_en   = form_row(fc, "End Date", 3); e_en.insert(0, "2026-12-05")
        
        tk.Frame(fc, bg=C["border"], height=1).grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        e_amt  = form_row(fc, "Deposit Amount ($)", 5); e_amt.insert(0, "100.00")
        
        log = log_box(fc, height=10)
        log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        def execute_tx(simulate_fail=False):
            log_clear(log)
            cid = get_id(e_cust.get()); vid = get_id(e_veh.get())
            st = e_st.get().strip(); en = e_en.get().strip()
            amt = e_amt.get().strip()
            
            if not all([cid, vid, st, en, amt]):
                log_write(log, "  ✗  All fields are required.", "err"); return

            new_res_id = next_id("RESERVATION", "reservation_id", 6600)
            new_pay_id = next_id("PAYMENT", "payment_id", 8600)

            conn = get_conn()
            if not conn: return

            try:
                # 1. START TRANSACTION
                conn.start_transaction()
                log_write(log, "▶ TRANSACTION STARTED", "warn")
                
                cur = conn.cursor()
                
                # 2. INSERT RESERVATION
                log_write(log, f"  [Step 1] Attempting to INSERT Reservation #{new_res_id}...", "info")
                cur.execute("""
                    INSERT INTO RESERVATION (reservation_id, customer_id, vehicle_id, start_date, end_date, status)
                    VALUES (%s, %s, %s, %s, %s, 'CONFIRMED')
                """, (new_res_id, cid, vid, st, en))
                log_write(log, "  ✔ Reservation inserted into DB memory.", "ok")
                
                # SIMULATE ERROR
                if simulate_fail:
                    log_write(log, f"  [Step 2] Attempting to process Payment of ${amt}...", "info")
                    log_write(log, "  💥 FATAL ERROR: Payment Gateway Timeout!", "err")
                    raise Exception("Payment Failed")
                
                # 3. INSERT PAYMENT
                log_write(log, f"  [Step 2] Attempting to process Payment of ${amt}...", "info")
                cur.execute("""
                    INSERT INTO PAYMENT (payment_id, reservation_id, amount, payment_type, status)
                    VALUES (%s, %s, %s, 'Credit Card', 'COMPLETED')
                """, (new_pay_id, new_res_id, float(amt)))
                log_write(log, "  ✔ Payment processed successfully.", "ok")

                # 4. COMMIT
                conn.commit()
                log_write(log, "\n✔ TRANSACTION COMMITTED SUCCESSFULLY!", "accent2")
                
            except Exception as e:
                # 5. ROLLBACK
                conn.rollback()
                log_write(log, f"\n✗ TRANSACTION ROLLED BACK.", "err")
                log_write(log, f"  Reason: {str(e)}", "err")  # <-- THIS PRINTS THE EXACT DB ERROR
                log_write(log, "  The Reservation was NOT saved to the database.", "err")
            finally:
                cur.close(); conn.close()
                ref_tables()

        btn(fc, "1. Execute & COMMIT (Success)", lambda: execute_tx(False), color=C["accent2"], width=30).grid(row=6, column=0, columnspan=2, pady=(10, 2))
        btn(fc, "2. Execute & ROLLBACK (Fail)", lambda: execute_tx(True), color=C["danger"], width=30).grid(row=7, column=0, columnspan=2, pady=(2, 10))

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "RESERVATIONS TABLE", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
        rf, rt = make_tree(rc, ["Res ID", "Cust", "Veh", "Start", "End"], heights=10)
        rf.pack(fill="both", expand=True, pady=4)
        
        label(rc, "PAYMENTS TABLE", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w", pady=(10,0))
        pf, pt = make_tree(rc, ["Pay ID", "Res ID", "Amount", "Type"], heights=10)
        pf.pack(fill="both", expand=True, pady=4)

        def ref_tables():
            c1, r1 = run_query("SELECT reservation_id, customer_id, vehicle_id, start_date, end_date FROM RESERVATION ORDER BY reservation_id DESC LIMIT 10")
            populate_tree(rt, c1, r1)
            c2, r2 = run_query("SELECT payment_id, reservation_id, amount, payment_type FROM PAYMENT ORDER BY payment_id DESC LIMIT 10")
            populate_tree(pt, c2, r2)
            
        btn(rc, "🔄 Refresh Tables", ref_tables, width=16).pack(anchor="w", pady=(5,0))
        ref_tables()

        return f

    def _tx_isolation(self, parent):
        f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

        hf = card_frame(f, padx=14, pady=10)
        hf.pack(fill="x", pady=(0, 10))
        tk.Label(hf, text="SCENARIO: Two employees try to update the EXACT SAME vehicle simultaneously.",
                 font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
        tk.Label(hf, text="ISOLATION: User 1 starts a transaction and modifies Vehicle 501. Before User 1 commits, User 2 tries to modify Vehicle 501.\n"
                          "Because of InnoDB Row-Level Locking, User 2 is BLOCKED and must wait, preventing data corruption.",
                 font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=1)

        lc = card_frame(body, padx=16, pady=16)
        lc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        e_veh = combo_row(lc, "Target Vehicle", 0, load_vehicles_all_no_status)
        
        log = log_box(lc, height=18)
        log.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        def execute_concurrency():
            log_clear(log)
            vid = get_id(e_veh.get())
            if not vid:
                log_write(log, "  ✗  Select a vehicle first.", "err"); return

            # Open two distinct connections to simulate two different users
            conn1 = get_conn()
            conn2 = get_conn()
            
            if not conn1 or not conn2: return

            try:
                cur1 = conn1.cursor()
                cur2 = conn2.cursor()

                # --- USER 1 ---
                log_write(log, "▶ USER 1: Starts Transaction...", "accent2")
                conn1.start_transaction()
                
                log_write(log, f"▶ USER 1: Updating Vehicle #{vid} to 'RENTED'...", "accent2")
                cur1.execute("UPDATE VEHICLE SET status = 'RENTED' WHERE vehicle_id = %s", (vid,))
                log_write(log, "▶ USER 1: Update executed. (Not committed yet). Row is now LOCKED.", "warn")
                
                # Force UI to update immediately before blocking
                self.update() 

                # --- USER 2 ---
                log_write(log, "\n▶ USER 2: Starts Transaction...", "accent")
                conn2.start_transaction()
                
                # Set a short timeout for the demo so we don't freeze the UI forever
                cur2.execute("SET SESSION innodb_lock_wait_timeout = 2")
                
                log_write(log, f"▶ USER 2: Attempting to update Vehicle #{vid} to 'UNDER_MAINTENANCE'...", "accent")
                log_write(log, "▶ USER 2: WAITING for lock... (UI will pause for 2 seconds)", "muted")
                self.update()

                try:
                    # This will block because User 1 holds the lock!
                    cur2.execute("UPDATE VEHICLE SET status = 'UNDER_MAINTENANCE' WHERE vehicle_id = %s", (vid,))
                except mysql.connector.Error as err:
                    log_write(log, f"\n💥 USER 2 CRASHED: {err}", "err")
                    log_write(log, "  Proof: The Database prevented concurrent modification!", "err")

                # --- CLEANUP ---
                log_write(log, "\n▶ USER 1: Rolling back transaction to release locks and clean up DB...", "info")
                conn1.rollback()
                log_write(log, "✔ Demo finished. Database is safe.", "ok")

            except Exception as e:
                log_write(log, f"System Error: {e}", "err")
            finally:
                if conn1.is_connected():
                    cur1.close(); conn1.close()
                if conn2.is_connected():
                    cur2.close(); conn2.close()

        btn(lc, "⚡ Simulate Concurrent Conflict", execute_concurrency, color=C["warn"], width=30).grid(row=1, column=0, columnspan=2, pady=(10, 2))

        rc = card_frame(body, padx=8, pady=8)
        rc.grid(row=0, column=1, sticky="nsew")
        label(rc, "SQL EXPLANATION", font=FONT_HEAD, fg=C["accent2"]).pack(anchor="w")
        
        sql_text = """
-- Connection 1 (User 1)
START TRANSACTION;
UPDATE vehicle 
SET status = 'RENTED' 
WHERE vehicle_id = 501;

-- Connection 2 (User 2) runs simultaneously:
START TRANSACTION;
-- Tries to update the same row
UPDATE vehicle 
SET status = 'UNDER_MAINTENANCE' 
WHERE vehicle_id = 501;
-- ❌ BLOCKS until Connection 1 finishes, 
-- or throws 'Lock wait timeout exceeded'

-- Connection 1 decides to Rollback
ROLLBACK; 
        """
        stb = scrolledtext.ScrolledText(rc, height=20, font=FONT_MONO, bg=C["bg"], fg=C["accent2"], relief="flat")
        stb.pack(fill="both", expand=True, pady=4)
        stb.insert("1.0", sql_text)
        stb.config(state="disabled")

        return f


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = CarRentalApp()
    app.mainloop()


# """
# =============================================================
#   CAR RENTAL SYSTEM — Desktop UI  (Tkinter)
#   Task 5 & 6 — TA / Instructor Demo
#   Install : pip install mysql-connector-python
#   Run     : python carui.py
# =============================================================
# """

# import tkinter as tk
# from tkinter import ttk, messagebox, scrolledtext
# import mysql.connector
# from mysql.connector import Error
# from datetime import date, datetime, timedelta

# # ─────────────────────────────────────────────
# #  DB CONFIG
# # ─────────────────────────────────────────────
# DB_CONFIG = {
#     "host":     "localhost",
#     "user":     "root",
#     "password": "Admin@12",
#     "database": "CarRentalSystem"
# }

# DAILY_RATES = {"SUV": 100, "Sedan": 70, "Hatchback": 50, "Truck": 90}

# # ─────────────────────────────────────────────
# #  COLOUR PALETTE
# # ─────────────────────────────────────────────
# C = {
#     "bg":       "#0F1117",
#     "sidebar":  "#161B27",
#     "card":     "#1C2333",
#     "border":   "#2A3350",
#     "accent":   "#3B82F6",
#     "accent2":  "#10B981",
#     "danger":   "#EF4444",
#     "warn":     "#F59E0B",
#     "text":     "#E2E8F0",
#     "muted":    "#64748B",
#     "heading":  "#F8FAFC",
#     "row_odd":  "#1C2333",
#     "row_even": "#1A2030",
#     "sel":      "#2D4A7A",
# }

# FONT_TITLE = ("Courier New", 13, "bold")
# FONT_HEAD  = ("Courier New", 10, "bold")
# FONT_BODY  = ("Courier New",  9)
# FONT_SMALL = ("Courier New",  8)
# FONT_MONO  = ("Courier New",  9)
# FONT_BIG   = ("Courier New", 16, "bold")

# # ─────────────────────────────────────────────
# #  DB HELPERS
# # ─────────────────────────────────────────────
# def get_conn():
#     try:
#         c = mysql.connector.connect(**DB_CONFIG)
#         if c.is_connected():
#             return c
#     except Error as e:
#         messagebox.showerror("DB Error", str(e))
#     return None

# def run_query(sql, params=()):
#     conn = get_conn()
#     if not conn:
#         return [], []
#     try:
#         cur = conn.cursor()
#         cur.execute(sql, params)
#         rows = cur.fetchall()
#         cols = [d[0] for d in cur.description] if cur.description else []
#         return cols, rows
#     except Error as e:
#         messagebox.showerror("Query Error", str(e))
#         return [], []
#     finally:
#         cur.close(); conn.close()

# def run_write(sql, params=()):
#     conn = get_conn()
#     if not conn:
#         return False, "No DB connection"
#     try:
#         cur = conn.cursor()
#         cur.execute(sql, params)
#         conn.commit()
#         return True, "OK"
#     except Error as e:
#         return False, e.msg
#     finally:
#         cur.close(); conn.close()

# def record_exists(table, pk_col, pk_val):
#     _, rows = run_query(f"SELECT 1 FROM `{table}` WHERE `{pk_col}` = %s", (pk_val,))
#     return len(rows) > 0

# def next_id(table, pk_col, base=1000, floor=None):
#     _, rows = run_query(
#         f"SELECT COALESCE(MAX(`{pk_col}`), %s) + 1 FROM `{table}`", (base,))
#     val = int(rows[0][0]) if rows else base + 1
#     if floor is not None:
#         val = max(val, floor + 1)
#     return val

# # ─────────────────────────────────────────────
# #  DATE / DATETIME HELPERS
# # ─────────────────────────────────────────────
# def parse_date(s):
#     try:
#         return datetime.strptime(s.strip(), "%Y-%m-%d").date()
#     except Exception:
#         return None

# def parse_datetime(s):
#     for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
#         try:
#             return datetime.strptime(s.strip(), fmt)
#         except Exception:
#             pass
#     return None

# def to_date(v):
#     if isinstance(v, datetime):
#         return v.date()
#     if isinstance(v, date):
#         return v
#     try:
#         return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
#     except Exception:
#         return None

# def to_datetime(v):
#     if isinstance(v, datetime):
#         return v
#     try:
#         return datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S")
#     except Exception:
#         return None

# # ─────────────────────────────────────────────
# #  BUSINESS LOGIC
# # ─────────────────────────────────────────────
# def vehicle_overlap_check(vid, start_str, end_str, exclude_res_id=None):
#     sql = """
#         SELECT reservation_id, start_date, end_date
#         FROM   RESERVATION
#         WHERE  vehicle_id  = %s
#           AND  status      = 'CONFIRMED'
#           AND  start_date <= %s
#           AND  end_date   >= %s
#     """
#     params = [vid, end_str, start_str]
#     if exclude_res_id:
#         sql += " AND reservation_id != %s"
#         params.append(exclude_res_id)
#     _, rows = run_query(sql, tuple(params))
#     return rows

# def customer_overlap_check(cust_id, start_str, end_str, exclude_res_id=None):
#     sql = """
#         SELECT reservation_id, vehicle_id, start_date, end_date
#         FROM   RESERVATION
#         WHERE  customer_id = %s
#           AND  status      = 'CONFIRMED'
#           AND  start_date <= %s
#           AND  end_date   >= %s
#     """
#     params = [cust_id, end_str, start_str]
#     if exclude_res_id:
#         sql += " AND reservation_id != %s"
#         params.append(exclude_res_id)
#     _, rows = run_query(sql, tuple(params))
#     return rows

# def customer_doc_status(cust_id):
#     _, docs = run_query(
#         "SELECT document_type, status, expiry_date "
#         "FROM DOCUMENT WHERE customer_id = %s",
#         (cust_id,))
#     _, valid = run_query(
#         "SELECT 1 FROM DOCUMENT "
#         "WHERE customer_id = %s AND status = 'VERIFIED' "
#         "AND expiry_date >= CURDATE() LIMIT 1",
#         (cust_id,))
#     return len(valid) > 0, docs

# def get_daily_rate(category):
#     return DAILY_RATES.get(category, 65)

# def calc_charge(category, disc_pct, pickup_dt, return_dt):
#     rate       = get_daily_rate(category)
#     disc       = float(disc_pct or 0) / 100.0
#     eff        = rate * (1.0 - disc)
#     total_days = max((return_dt.date() - pickup_dt.date()).days, 1)
    
#     return {
#         "rate":      rate,
#         "disc_pct":  disc_pct,
#         "eff":       eff,
#         "days":      total_days,
#         "total":     total_days * eff,
#     }

# def get_balance(rental_id):
#     _, tr = run_query("SELECT total_amount FROM RENTAL WHERE rental_id = %s", (rental_id,))
#     total = float(tr[0][0]) if tr and tr[0][0] is not None else 0.0
#     _, pr = run_query(
#         "SELECT COALESCE(SUM(amount),0) FROM PAYMENT "
#         "WHERE rental_id = %s AND status = 'COMPLETED'", (rental_id,))
#     paid = float(pr[0][0]) if pr else 0.0
#     return total, paid, max(total - paid, 0.0)

# # ─────────────────────────────────────────────
# #  DROPDOWN LOADERS
# # ─────────────────────────────────────────────
# _EM = "\u2014"

# def _em(pk, label):
#     return f"{pk} {_EM} {label}"

# def load_customers():
#     _, r = run_query(
#         "SELECT customer_id, CONCAT(first_name,' ',last_name) "
#         "FROM CUSTOMER ORDER BY customer_id")
#     return [_em(x[0], x[1]) for x in r]

# def load_vehicles_available():
#     _, r = run_query(
#         "SELECT vehicle_id, model, category FROM VEHICLE "
#         "WHERE status = 'AVAILABLE' ORDER BY vehicle_id")
#     return [_em(x[0], f"{x[1]} ({x[2]})") for x in r]

# def load_vehicles_all_no_status():
#     _, r = run_query(
#         "SELECT vehicle_id, model, category FROM VEHICLE ORDER BY vehicle_id")
#     return [_em(x[0], f"{x[1]} ({x[2]})") for x in r]

# def load_branches():
#     _, r = run_query(
#         "SELECT branch_id, branch_name FROM BRANCH ORDER BY branch_id")
#     return [_em(x[0], x[1]) for x in r]

# def load_res_confirmed():
#     _, r = run_query("""
#         SELECT r.reservation_id,
#                CONCAT(c.first_name,' ',c.last_name),
#                r.vehicle_id, r.start_date, r.end_date
#         FROM   RESERVATION r
#         JOIN   CUSTOMER c ON r.customer_id = c.customer_id
#         WHERE  r.status = 'CONFIRMED'
#         ORDER  BY r.reservation_id
#     """)
#     return [_em(x[0], f"{x[1]} | Veh#{x[2]} ({str(x[3])[:10]}→{str(x[4])[:10]})") for x in r]

# def load_res_all():
#     _, r = run_query(
#         "SELECT reservation_id, customer_id, vehicle_id, status "
#         "FROM RESERVATION ORDER BY reservation_id DESC")
#     return [_em(x[0], f"Cust#{x[1]} | Veh#{x[2]} ({x[3]})") for x in r]

# def load_rentals_active():
#     _, r = run_query("""
#         SELECT r.rental_id, v.model,
#                CONCAT(c.first_name,' ',c.last_name), r.pickup_date
#         FROM   RENTAL r
#         JOIN   VEHICLE v     ON r.vehicle_id      = v.vehicle_id
#         JOIN   RESERVATION s ON r.reservation_id  = s.reservation_id
#         JOIN   CUSTOMER c    ON s.customer_id     = c.customer_id
#         WHERE  r.status = 'ACTIVE'
#         ORDER  BY r.rental_id
#     """)
#     return [_em(x[0], f"{x[1]} | {x[2]} | {str(x[3])[:10]}") for x in r]

# def load_rentals_all():
#     _, r = run_query("""
#         SELECT r.rental_id, v.model,
#                CONCAT(c.first_name,' ',c.last_name), r.status
#         FROM   RENTAL r
#         JOIN   VEHICLE v     ON r.vehicle_id      = v.vehicle_id
#         JOIN   RESERVATION s ON r.reservation_id  = s.reservation_id
#         JOIN   CUSTOMER c    ON s.customer_id     = c.customer_id
#         ORDER  BY r.rental_id DESC
#     """)
#     return [_em(x[0], f"{x[1]} | {x[2]} ({x[3]})") for x in r]

# PAYMENT_TYPES = ["Credit Card", "Debit Card", "Cash", "Bank Transfer", "UPI"]

# def get_id(val):
#     if val and _EM in val:
#         return val.split(_EM)[0].strip()
#     return val.strip() if val else ""

# # ─────────────────────────────────────────────
# #  VALIDATION HELPERS
# # ─────────────────────────────────────────────
# def validate_reservation(log, cid, vid, st_raw, en_raw):
#     if not cid:
#         log_write(log, "  ✗  Please select a Customer.", "err");  return None, None
#     if not vid:
#         log_write(log, "  ✗  Please select a Vehicle.", "err");   return None, None
#     if not st_raw:
#         log_write(log, "  ✗  Start Date is required.  Format: YYYY-MM-DD", "err"); return None, None
#     if not en_raw:
#         log_write(log, "  ✗  End Date is required.  Format: YYYY-MM-DD", "err");   return None, None

#     st = parse_date(st_raw)
#     if st is None:
#         log_write(log, f"  ✗  '{st_raw}' is not a valid date. Use YYYY-MM-DD", "err")
#         return None, None

#     en = parse_date(en_raw)
#     if en is None:
#         log_write(log, f"  ✗  '{en_raw}' is not a valid date. Use YYYY-MM-DD", "err")
#         return None, None

#     if en < st:
#         log_write(log, "  ✗  End Date cannot be before Start Date.", "err")
#         log_write(log, f"        Start: {st}   End: {en}", "err"); return None, None
#     if en == st:
#         log_write(log, "  ✗  Minimum rental period is 1 day (End must be after Start).", "err")
#         return None, None
#     if st < date.today():
#         log_write(log, f"  ⚠  Start Date {st} is in the past.", "warn")

#     if not record_exists("CUSTOMER", "customer_id", cid):
#         log_write(log, f"  ✗  Customer #{cid} not found in DB.", "err"); return None, None
#     if not record_exists("VEHICLE", "vehicle_id", vid):
#         log_write(log, f"  ✗  Vehicle #{vid} not found in DB.", "err"); return None, None

#     cust_conflicts = customer_overlap_check(cid, st_raw, en_raw)
#     if cust_conflicts:
#         log_write(log, "  ══" * 22, "err")
#         log_write(log, "  ✗  CUSTOMER DOUBLE-BOOKING PREVENTED", "err")
#         log_write(log, f"     Customer #{cid} already has a CONFIRMED reservation", "err")
#         log_write(log, "     whose dates overlap the requested period:", "err")
#         for row in cust_conflicts:
#             log_write(log,
#                 f"        Res #{row[0]}  |  Vehicle #{row[1]}  "
#                 f"|  {str(row[2])[:10]} → {str(row[3])[:10]}", "err")
#         log_write(log, "     Choose different dates or a different customer.", "err")
#         log_write(log, "  ══" * 22, "err")
#         return None, None

#     return st, en

# def validate_rental_start(log, res_id, bid, dt_raw):
#     if not res_id:
#         log_write(log, "  ✗  Please select a Reservation.", "err"); return None
#     if not bid:
#         log_write(log, "  ✗  Please select a Pickup Branch.", "err"); return None
#     if not dt_raw:
#         log_write(log, "  ✗  Pickup DateTime is required.", "err"); return None

#     dt = parse_datetime(dt_raw)
#     if dt is None:
#         log_write(log, f"  ✗  '{dt_raw}' is not a valid datetime.", "err")
#         log_write(log, "        Use YYYY-MM-DD HH:MM:SS   e.g. 2026-04-01 10:00:00", "err")
#         return None

#     if not record_exists("RESERVATION", "reservation_id", res_id):
#         log_write(log, f"  ✗  Reservation #{res_id} not found.", "err"); return None
#     if not record_exists("BRANCH", "branch_id", bid):
#         log_write(log, f"  ✗  Branch #{bid} not found.", "err"); return None
#     return dt

# def validate_rental_end(log, rid, bid, dt_raw):
#     if not rid:
#         log_write(log, "  ✗  Please select an Active Rental.", "err"); return None, None, None
#     if not bid:
#         log_write(log, "  ✗  Please select a Return Branch.", "err");  return None, None, None
#     if not dt_raw:
#         log_write(log, "  ✗  Return DateTime is required.", "err");    return None, None, None

#     ret_dt = parse_datetime(dt_raw)
#     if ret_dt is None:
#         log_write(log, f"  ✗  '{dt_raw}' is not a valid datetime.", "err")
#         log_write(log, "        Use YYYY-MM-DD HH:MM:SS   e.g. 2026-04-05 15:00:00", "err")
#         return None, None, None

#     if not record_exists("RENTAL", "rental_id", rid):
#         log_write(log, f"  ✗  Rental #{rid} not found.", "err"); return None, None, None
#     if not record_exists("BRANCH", "branch_id", bid):
#         log_write(log, f"  ✗  Branch #{bid} not found.", "err"); return None, None, None

#     _, r = run_query(
#         "SELECT status, vehicle_id, pickup_date FROM RENTAL WHERE rental_id = %s", (rid,))
#     if not r:
#         log_write(log, "  ✗  Could not read rental row.", "err"); return None, None, None

#     rstatus, veh_id, pickup_raw = r[0]
#     if rstatus != "ACTIVE":
#         log_write(log, f"  ✗  Rental #{rid} is '{rstatus}'. Only ACTIVE rentals can be completed.", "err")
#         return None, None, None

#     pickup_dt = to_datetime(pickup_raw)
#     if pickup_dt and ret_dt <= pickup_dt:
#         log_write(log, "  ✗  Return DateTime must be AFTER Pickup DateTime.", "err")
#         log_write(log, f"        Pickup : {pickup_dt}", "err")
#         log_write(log, f"        Return : {ret_dt}", "err")
#         return None, None, None

#     return ret_dt, veh_id, pickup_dt

# # ─────────────────────────────────────────────
# #  WIDGET FACTORY HELPERS
# # ─────────────────────────────────────────────
# def card_frame(parent, padx=8, pady=8, bg=None):
#     return tk.Frame(parent, bg=bg or C["card"], padx=padx, pady=pady)

# def label(parent, text, font=FONT_BODY, fg=None, bg=None, **kw):
#     kw.pop("fg", None); kw.pop("bg", None)
#     return tk.Label(parent, text=text, font=font,
#                     fg=fg or C["text"], bg=bg or C["card"], **kw)

# def heading(parent, text, fg=None, bg=None, **kw):
#     return tk.Label(parent, text=text, font=FONT_TITLE,
#                     fg=fg or C["heading"], bg=bg or C["card"], **kw)

# def btn(parent, text, cmd, color=None, width=18, **kw):
#     b = tk.Button(parent, text=text, command=cmd,
#                   font=FONT_HEAD,
#                   bg=color or C["accent"], fg=C["heading"],
#                   activebackground=C["border"], activeforeground=C["heading"],
#                   relief="flat", cursor="hand2", width=width, pady=6, **kw)
#     b.bind("<Enter>", lambda e: b.config(bg=C["border"]))
#     b.bind("<Leave>", lambda e: b.config(bg=color or C["accent"]))
#     return b

# def entry(parent, width=26, **kw):
#     return tk.Entry(parent, font=FONT_BODY,
#                     bg=C["border"], fg=C["text"],
#                     insertbackground=C["text"],
#                     relief="flat", width=width, **kw)

# def _apply_combo_style():
#     s = ttk.Style()
#     s.configure("Car.TCombobox",
#                 fieldbackground=C["border"], background=C["border"],
#                 foreground=C["text"], selectbackground=C["sel"],
#                 selectforeground=C["heading"], arrowcolor=C["accent"])
#     s.map("Car.TCombobox",
#           fieldbackground=[("readonly", C["border"]), ("disabled", C["bg"])],
#           foreground=[("readonly", C["text"])])

# def combo(parent, loader, width=34, **kw):
#     _apply_combo_style()
#     cb = ttk.Combobox(parent, font=FONT_BODY, width=width,
#                       style="Car.TCombobox", **kw)
#     cb["values"] = loader()
#     def _refresh(event=None):
#         cur = cb.get()
#         cb["values"] = loader()
#         if cur:
#             cb.set(cur)
#     cb.bind("<Button-1>", _refresh)
#     cb.bind("<FocusIn>",  _refresh)
#     return cb

# def combo_row(parent, lbl_text, row, loader, col=0, width=34):
#     label(parent, lbl_text + ":", bg=C["card"]).grid(
#         row=row, column=col, sticky="w", padx=(0, 8), pady=4)
#     cb = combo(parent, loader, width=width)
#     cb.grid(row=row, column=col + 1, sticky="w", pady=4)
#     return cb

# def static_combo_row(parent, lbl_text, row, values, col=0, width=28):
#     _apply_combo_style()
#     label(parent, lbl_text + ":", bg=C["card"]).grid(
#         row=row, column=col, sticky="w", padx=(0, 8), pady=4)
#     cb = ttk.Combobox(parent, font=FONT_BODY, width=width,
#                       style="Car.TCombobox", values=values)
#     cb.grid(row=row, column=col + 1, sticky="w", pady=4)
#     return cb

# def form_row(parent, lbl_text, row, col=0, w=25):
#     label(parent, lbl_text + ":", bg=C["card"]).grid(
#         row=row, column=col, sticky="w", padx=(0, 8), pady=4)
#     e = entry(parent, width=w)
#     e.grid(row=row, column=col + 1, sticky="w", pady=4)
#     return e

# def hint_row(parent, text, row, col=1):
#     label(parent, "  " + text, font=FONT_SMALL,
#           fg=C["muted"], bg=C["card"]).grid(row=row, column=col, sticky="w")

# def db_hint_row(parent, row=0):
#     label(parent,
#           "  ↓  Click any dropdown to auto-refresh from DB",
#           font=FONT_SMALL, fg=C["muted"], bg=C["card"]).grid(
#           row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))

# def divider(parent, pady=6):
#     tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=pady)

# def make_tree(parent, cols, heights=12):
#     style = ttk.Style(); style.theme_use("clam")
#     style.configure("Car.Treeview",
#                     background=C["row_odd"], foreground=C["text"],
#                     fieldbackground=C["row_odd"], rowheight=24, font=FONT_BODY)
#     style.configure("Car.Treeview.Heading",
#                     background=C["border"], foreground=C["accent"],
#                     font=FONT_HEAD, relief="flat")
#     style.map("Car.Treeview",
#               background=[("selected", C["sel"])],
#               foreground=[("selected", C["heading"])])
#     frame = tk.Frame(parent, bg=C["card"])
#     tree  = ttk.Treeview(frame, columns=cols, show="headings",
#                          style="Car.Treeview", height=heights)
#     vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
#     hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
#     tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
#     for col in cols:
#         tree.heading(col, text=col)
#         tree.column(col, width=max(len(col) * 11, 80), anchor="w")
#     tree.grid(row=0, column=0, sticky="nsew")
#     vsb.grid(row=0, column=1, sticky="ns")
#     hsb.grid(row=1, column=0, sticky="ew")
#     frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
#     return frame, tree

# def populate_tree(tree, cols, rows):
#     tree.delete(*tree.get_children())
#     for i, row in enumerate(rows):
#         vals = [str(v) if v is not None else "NULL" for v in row]
#         tag  = "even" if i % 2 == 0 else "odd"
#         tree.insert("", "end", values=vals, tags=(tag,))
#     tree.tag_configure("even", background=C["row_even"])
#     tree.tag_configure("odd",  background=C["row_odd"])

# def log_box(parent, height=8):
#     tb = scrolledtext.ScrolledText(
#         parent, height=height, font=FONT_MONO,
#         bg=C["bg"], fg=C["text"], insertbackground=C["text"],
#         relief="flat", wrap="word", state="disabled")
#     tb.tag_config("ok",      foreground=C["accent2"])
#     tb.tag_config("err",     foreground=C["danger"])
#     tb.tag_config("warn",    foreground=C["warn"])
#     tb.tag_config("info",    foreground=C["accent"])
#     tb.tag_config("heading", foreground=C["heading"], font=FONT_HEAD)
#     return tb

# def log_write(tb, text, tag="info"):
#     tb.config(state="normal")
#     tb.insert("end", text + "\n", tag)
#     tb.see("end")
#     tb.config(state="disabled")

# def log_clear(tb):
#     tb.config(state="normal")
#     tb.delete("1.0", "end")
#     tb.config(state="disabled")

# def info_block_grid(parent, row, title, fields):
#     f = tk.Frame(parent, bg=C["border"], padx=12, pady=10)
#     f.grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
#     tk.Label(f, text=title, font=FONT_HEAD,
#              fg=C["warn"], bg=C["border"]).pack(anchor="w", pady=(0, 6))
#     for lbl, var, clr in fields:
#         row2 = tk.Frame(f, bg=C["border"]); row2.pack(fill="x", pady=1)
#         tk.Label(row2, text=lbl, font=FONT_SMALL, fg=C["muted"],
#                  bg=C["border"], width=18, anchor="w").pack(side="left")
#         tk.Label(row2, textvariable=var, font=FONT_MONO,
#                  fg=clr, bg=C["border"]).pack(side="left", padx=4)
#     return f

# def make_scrollable(parent, bg=None):
#     bg = bg or C["bg"]
#     canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
#     vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
#     inner = tk.Frame(canvas, bg=bg)
#     win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

#     def _on_inner_configure(e):
#         canvas.configure(scrollregion=canvas.bbox("all"))

#     def _on_canvas_configure(e):
#         canvas.itemconfig(win_id, width=e.width)

#     inner.bind("<Configure>", _on_inner_configure)
#     canvas.bind("<Configure>", _on_canvas_configure)
#     canvas.configure(yscrollcommand=vsb.set)

#     canvas.pack(side="left", fill="both", expand=True)
#     vsb.pack(side="right", fill="y")

#     def _mw(e):
#         canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
#     def _mw_linux_up(e):
#         canvas.yview_scroll(-1, "units")
#     def _mw_linux_down(e):
#         canvas.yview_scroll(1, "units")

#     def _bind(e):
#         canvas.bind_all("<MouseWheel>",  _mw)
#         canvas.bind_all("<Button-4>",    _mw_linux_up)
#         canvas.bind_all("<Button-5>",    _mw_linux_down)
#     def _unbind(e):
#         canvas.unbind_all("<MouseWheel>")
#         canvas.unbind_all("<Button-4>")
#         canvas.unbind_all("<Button-5>")

#     canvas.bind("<Enter>", _bind)
#     canvas.bind("<Leave>", _unbind)
#     return inner

# # ─────────────────────────────────────────────
# #  MAIN APPLICATION
# # ─────────────────────────────────────────────
# class CarRentalApp(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Car Rental Management System — Task 5 & 6 Demo")
#         self.geometry("1380x840")
#         self.minsize(1100, 700)
#         self.configure(bg=C["bg"])
#         self._build()
#         self._show("dashboard")

#     def _build(self):
#         self.sidebar = tk.Frame(self, bg=C["sidebar"], width=215)
#         self.sidebar.pack(side="left", fill="y")
#         self.sidebar.pack_propagate(False)
#         self.main = tk.Frame(self, bg=C["bg"])
#         self.main.pack(side="left", fill="both", expand=True)
#         self.status_var = tk.StringVar(value="◉  Connected to CarRentalSystem")
#         tk.Label(self, textvariable=self.status_var,
#                  font=FONT_SMALL, bg=C["border"], fg=C["muted"],
#                  anchor="w", padx=10).pack(side="bottom", fill="x")

#         self._build_sidebar()
#         self.container = tk.Frame(self.main, bg=C["bg"])
#         self.container.pack(fill="both", expand=True, padx=12, pady=12)

#         self.panels = {}
#         builders = [
#             ("dashboard",   self._panel_dashboard),
#             ("cars",        self._panel_cars),
#             ("customers",   self._panel_customers),
#             ("reservation", self._panel_reservation),
#             ("start",       self._panel_start),
#             ("end",         self._panel_end),
#             ("payment",     self._panel_payment),
#             ("active",      self._panel_active),
#             ("revenue",     self._panel_revenue),
#             ("triggers",    self._panel_triggers),
#             ("transactions", self._panel_transactions), # Added Task 6 Panel
#         ]
#         for key, builder in builders:
#             self.panels[key] = builder()

#     def _build_sidebar(self):
#         tk.Label(self.sidebar, text="🚗 CAR RENTAL",
#                  font=("Courier New", 12, "bold"),
#                  fg=C["accent"], bg=C["sidebar"], pady=18).pack(fill="x")
#         tk.Label(self.sidebar, text="MGMT SYSTEM",
#                  font=FONT_SMALL, fg=C["muted"], bg=C["sidebar"]).pack()
#         tk.Frame(self.sidebar, bg=C["border"], height=1).pack(fill="x", pady=10)

#         nav = [
#             ("⬡  Dashboard",        "dashboard"),
#             ("◈  Available Cars",    "cars"),
#             ("◉  Customers & Docs",  "customers"),
#             ("◎  Make Reservation",  "reservation"),
#             ("▶  Start Rental",      "start"),
#             ("■  Complete Rental",   "end"),
#             ("$  Record Payment",    "payment"),
#             ("≡  Active Rentals",    "active"),
#             ("◈  Revenue Report",    "revenue"),
#         ]
#         self._nav_btns = {}
#         for txt, key in nav:
#             b = tk.Button(self.sidebar, text=txt, font=FONT_BODY,
#                           bg=C["sidebar"], fg=C["text"],
#                           activebackground=C["card"], activeforeground=C["heading"],
#                           relief="flat", anchor="w", padx=18, pady=8, cursor="hand2",
#                           command=lambda k=key: self._show(k))
#             b.pack(fill="x")
#             self._nav_btns[key] = b

#         tk.Frame(self.sidebar, bg=C["border"], height=1).pack(fill="x", pady=10)
        
#         # Trigger Demo Button
#         tb = tk.Button(self.sidebar, text="⚡ TRIGGER DEMO",
#                        font=FONT_HEAD, bg=C["warn"], fg=C["bg"],
#                        activebackground=C["accent2"], relief="flat",
#                        anchor="w", padx=18, pady=10, cursor="hand2",
#                        command=lambda: self._show("triggers"))
#         tb.pack(fill="x", padx=8, pady=4)
#         self._nav_btns["triggers"] = tb

#         # Task 6 Transactions Demo Button
#         txb = tk.Button(self.sidebar, text="🔄 TRANSACTIONS",
#                        font=FONT_HEAD, bg=C["accent2"], fg=C["bg"],
#                        activebackground=C["warn"], relief="flat",
#                        anchor="w", padx=18, pady=10, cursor="hand2",
#                        command=lambda: self._show("transactions"))
#         txb.pack(fill="x", padx=8, pady=4)
#         self._nav_btns["transactions"] = txb

#     def _show(self, key):
#         for p in self.panels.values():
#             p.pack_forget()
#         self.panels[key].pack(fill="both", expand=True)
#         for k, b in self._nav_btns.items():
#             if k == "triggers":
#                 b.config(bg=C["warn"] if key == k else C["sidebar"], fg=C["bg"] if key == k else C["text"])
#             elif k == "transactions":
#                 b.config(bg=C["accent2"] if key == k else C["sidebar"], fg=C["bg"] if key == k else C["text"])
#             else:
#                 b.config(bg=C["accent"] if key == k else C["sidebar"], fg=C["heading"] if key == k else C["text"])
#         self.status_var.set(f"◉  Viewing: {key.replace('_',' ').title()}")

#     # ─────────────────────────────────────────
#     #  DASHBOARD
#     # ─────────────────────────────────────────
#     def _panel_dashboard(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "CAR RENTAL MANAGEMENT SYSTEM",
#                 fg=C["accent"], bg=C["bg"]).pack(pady=(10, 2))
#         label(p, "Task 5 & 6 — TA / Instructor Demo Interface",
#               fg=C["muted"], bg=C["bg"]).pack(pady=(0, 20))

#         sf = tk.Frame(p, bg=C["bg"]); sf.pack(fill="x", pady=10)
#         self._stat_vars = {}
#         stats = [
#             ("Customers",      "SELECT COUNT(*) FROM CUSTOMER",                      C["accent"]),
#             ("Vehicles",       "SELECT COUNT(*) FROM VEHICLE",                       C["accent2"]),
#             ("Reservations",   "SELECT COUNT(*) FROM RESERVATION",                   C["warn"]),
#             ("Active Rentals", "SELECT COUNT(*) FROM RENTAL WHERE status='ACTIVE'", C["danger"]),
#         ]
#         for i, (title, sql, color) in enumerate(stats):
#             card = tk.Frame(sf, bg=C["card"], padx=20, pady=14)
#             card.grid(row=0, column=i, padx=8, sticky="ew")
#             sf.columnconfigure(i, weight=1)
#             v = tk.StringVar(value="…")
#             self._stat_vars[title] = (v, sql)
#             tk.Label(card, textvariable=v, font=FONT_BIG,
#                      fg=color, bg=C["card"]).pack()
#             tk.Label(card, text=title, font=FONT_SMALL,
#                      fg=C["muted"], bg=C["card"]).pack()

#         btn(p, "🔄  Refresh Stats", self._refresh_dashboard,
#             width=22).pack(pady=14)

#         info = tk.Frame(p, bg=C["card"], padx=20, pady=16)
#         info.pack(fill="x", padx=4, pady=8)
#         label(info, "TRIGGERS & RULES IMPLEMENTED", font=FONT_HEAD,
#               fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Frame(info, bg=C["border"], height=1).pack(fill="x", pady=6)
#         tdata = [
#             ("T1",  "BEFORE INSERT → RESERVATION", "Blocks overlapping date bookings for the same vehicle"),
#             ("T2",  "BEFORE INSERT → RENTAL",      "Blocks rental if customer has NO valid, unexpired VERIFIED document"),
#             ("T3",  "AFTER INSERT  → RENTAL",      "Auto-sets vehicle status → RENTED on pickup"),
#             ("T4",  "AFTER UPDATE  → RENTAL",      "Auto-sets vehicle status → AVAILABLE on return"),
#             ("★",   "APP RULE — RESERVATION",      "Customer double-booking blocked — no two overlapping reservations per customer"),
#         ]
#         for tid, event, desc in tdata:
#             rf = tk.Frame(info, bg=C["card"]); rf.pack(fill="x", pady=2)
#             clr = C["accent2"] if tid == "★" else C["warn"]
#             tk.Label(rf, text=f"  {tid} ", font=FONT_HEAD,
#                      fg=C["bg"], bg=clr, padx=4).pack(side="left")
#             tk.Label(rf, text=f"  {event}", font=FONT_MONO,
#                      fg=C["accent"], bg=C["card"],
#                      width=32, anchor="w").pack(side="left")
#             tk.Label(rf, text=desc, font=FONT_BODY,
#                      fg=C["text"], bg=C["card"]).pack(side="left")

#         self._refresh_dashboard()
#         return p

#     def _refresh_dashboard(self):
#         for title, (var, sql) in self._stat_vars.items():
#             _, rows = run_query(sql)
#             var.set(str(rows[0][0]) if rows else "?")

#     # ─────────────────────────────────────────
#     #  AVAILABLE CARS
#     # ─────────────────────────────────────────
#     def _panel_cars(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "AVAILABLE VEHICLES", bg=C["bg"]).pack(anchor="w", pady=(0, 8))
#         tf, tree = make_tree(
#             p, ["ID", "Reg No", "Model", "Category", "Fuel", "Status"],
#             heights=18)
#         tf.pack(fill="both", expand=True)
#         def ref():
#             c, r = run_query(
#                 "SELECT vehicle_id, registration_no, model, category, "
#                 "fuel_type, status FROM VEHICLE WHERE status='AVAILABLE' "
#                 "ORDER BY category, model")
#             populate_tree(tree, c, r)
#         btn(p, "🔄  Refresh", ref, width=16).pack(pady=8, anchor="w")
#         ref()
#         return p

#     # ─────────────────────────────────────────
#     #  CUSTOMERS & DOCUMENTS
#     # ─────────────────────────────────────────
#     def _panel_customers(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "CUSTOMERS & DOCUMENTS", bg=C["bg"]).pack(
#             anchor="w", pady=(0, 8))
#         top = tk.Frame(p, bg=C["bg"]); top.pack(fill="both", expand=True)
#         top.columnconfigure(0, weight=2); top.columnconfigure(1, weight=3)

#         lf = card_frame(top, padx=6, pady=6)
#         lf.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
#         label(lf, "CUSTOMERS", font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
#         cf, ct = make_tree(lf, ["ID", "Name", "Email", "Membership"], heights=16)
#         cf.pack(fill="both", expand=True, pady=4)

#         rf = card_frame(top, padx=6, pady=6)
#         rf.grid(row=0, column=1, sticky="nsew")
#         label(rf, "DOCUMENTS  (click a customer row →)",
#               font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
#         df, dt = make_tree(
#             rf, ["Doc ID", "Type", "Number", "Expiry", "Status"],
#             heights=16)
#         df.pack(fill="both", expand=True, pady=4)

#         def load_cust():
#             c, r = run_query("""
#                 SELECT cu.customer_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        cu.email, m.membership_type
#                 FROM   CUSTOMER cu
#                 LEFT JOIN MEMBERSHIP m ON cu.membership_id = m.membership_id
#                 ORDER  BY cu.customer_id""")
#             populate_tree(ct, c, r)

#         def on_sel(event):
#             sel = ct.selection()
#             if not sel: return
#             cid = ct.item(sel[0])["values"][0]
#             c, r = run_query("""
#                 SELECT document_id, document_type, document_number,
#                        expiry_date, status
#                 FROM   DOCUMENT WHERE customer_id = %s""", (cid,))
#             populate_tree(dt, c, r)
#             for ch in dt.get_children():
#                 vals = dt.item(ch)["values"]
#                 st = vals[4] if len(vals) > 4 else ""
#                 if st == "VERIFIED":
#                     dt.item(ch, tags=("ver",))
#                 elif st in ("EXPIRED", "REJECTED"):
#                     dt.item(ch, tags=("bad",))
#                 else:
#                     dt.item(ch, tags=("wrn",))
#             dt.tag_configure("ver", foreground=C["accent2"])
#             dt.tag_configure("bad", foreground=C["danger"])
#             dt.tag_configure("wrn", foreground=C["warn"])

#         ct.bind("<<TreeviewSelect>>", on_sel)
#         btn(lf, "🔄  Refresh", load_cust, width=16).pack(pady=4, anchor="w")
#         load_cust()
#         return p

#     # ─────────────────────────────────────────
#     #  MAKE RESERVATION
#     # ─────────────────────────────────────────
#     def _panel_reservation(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "MAKE A RESERVATION", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
#         label(p, "T1 blocks overlapping vehicle bookings  •  App blocks customer double-bookings.",
#               fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

#         body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=20, pady=20)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         label(fc, "RESERVATION FORM", font=FONT_HEAD,
#               fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
#         db_hint_row(fc, row=1)
#         e_cust = combo_row(fc, "Customer",   2, load_customers)
#         e_veh  = combo_row(fc, "Vehicle",    3, load_vehicles_available)
#         e_st   = form_row (fc, "Start Date", 4)
#         hint_row(fc, "YYYY-MM-DD   e.g. 2026-05-01", 5)
#         e_en   = form_row (fc, "End Date",   6)
#         hint_row(fc, "YYYY-MM-DD   must be after Start Date", 7)
#         log = log_box(fc, height=8)
#         log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))

#         def do():
#             log_clear(log)
#             cid = get_id(e_cust.get()); vid = get_id(e_veh.get())
#             st_r = e_st.get().strip();   en_r = e_en.get().strip()
#             st, en = validate_reservation(log, cid, vid, st_r, en_r)
#             if st is None: return

#             conflicts = vehicle_overlap_check(vid, st_r, en_r)
#             if conflicts:
#                 log_write(log, "  ══" * 22, "err")
#                 log_write(log, "  ✗  VEHICLE BOOKING CONFLICT:", "err")
#                 for row in conflicts:
#                     log_write(log, f"      Res #{row[0]}   {str(row[1])[:10]} → {str(row[2])[:10]}", "err")
#                 log_write(log, "  Choose different dates or a different vehicle.", "err")
#                 log_write(log, "  ══" * 22, "err")
#                 log_write(log, "  Forwarding to DB — Trigger 1 will also block it.", "warn")

#             new_id = next_id("RESERVATION", "reservation_id", 6000)
#             ok, msg = run_write("""
#                 INSERT INTO RESERVATION
#                     (reservation_id, customer_id, vehicle_id,
#                      start_date, end_date, status)
#                 VALUES (%s,%s,%s,%s,%s,'CONFIRMED')
#             """, (new_id, cid, vid, st_r, en_r))

#             if ok:
#                 log_write(log, "  ✔  Reservation confirmed!", "ok")
#                 log_write(log, f"     ID #{new_id}   {e_cust.get()[:30]}", "ok")
#                 log_write(log, f"     Period : {st}  →  {en}", "ok")
#                 ref_res()
#             else:
#                 if "TRIGGER BLOCKED" in msg:
#                     log_write(log, "  ══" * 22, "err")
#                     log_write(log, "  TRIGGER 1 FIRED ✔ — DB-level overlap blocked!", "err")
#                     log_write(log, f"  {msg}", "err")
#                     log_write(log, "  ══" * 22, "err")
#                 else:
#                     log_write(log, f"  ✗  {msg}", "err")

#         btn(fc, "✓  Confirm Reservation", do,
#             color=C["accent2"], width=26).grid(
#             row=9, column=0, columnspan=2, pady=12)

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "EXISTING RESERVATIONS", font=FONT_HEAD,
#               fg=C["muted"]).pack(anchor="w")
#         rf, rt = make_tree(
#             rc, ["Res ID", "Cust", "Veh", "Start", "End", "Status"],
#             heights=18)
#         rf.pack(fill="both", expand=True, pady=4)

#         def ref_res():
#             c, r = run_query("""
#                 SELECT reservation_id, customer_id, vehicle_id,
#                        start_date, end_date, status
#                 FROM   RESERVATION ORDER BY reservation_id DESC""")
#             populate_tree(rt, c, r)

#         btn(rc, "🔄  Refresh", ref_res, width=14).pack(anchor="w")
#         ref_res()
#         return p

#     # ─────────────────────────────────────────
#     #  START RENTAL
#     # ─────────────────────────────────────────
#     def _panel_start(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "START A RENTAL  (PICKUP)", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
#         label(p, "T2 checks documents  •  T3 flips vehicle → RENTED",
#               fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

#         body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=20, pady=20)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         label(fc, "PICKUP FORM", font=FONT_HEAD,
#               fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,4))
#         db_hint_row(fc, row=1)
#         e_res    = combo_row(fc, "Reservation",   2, load_res_confirmed)
#         e_branch = combo_row(fc, "Pickup Branch", 3, load_branches)
#         e_dt     = form_row (fc, "Pickup DateTime", 4, w=25)
#         hint_row(fc, "YYYY-MM-DD HH:MM:SS   e.g. 2026-04-01 10:00:00", 5)

#         rv = {k: tk.StringVar(value="—") for k in ["cust","veh","from","to","rate"]}
#         info_block_grid(fc, 6, "RESERVATION PREVIEW", [
#             ("Customer    :", rv["cust"], C["text"]),
#             ("Vehicle     :", rv["veh"],  C["accent"]),
#             ("Booked From :", rv["from"], C["text"]),
#             ("Booked To   :", rv["to"],   C["text"]),
#             ("Eff. Rate   :", rv["rate"], C["accent2"]),
#         ])

#         vsv = {k: tk.StringVar(value="—") for k in ["vid", "bef", "aft"]}
#         info_block_grid(fc, 7, "VEHICLE STATUS TRACKER  (T3)", [
#             ("Vehicle # :", vsv["vid"], C["accent"]),
#             ("BEFORE    :", vsv["bef"], C["warn"]),
#             ("AFTER     :", vsv["aft"], C["accent2"]),
#         ])

#         log = log_box(fc, height=4)
#         log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 0))

#         def on_res_select(event=None):
#             rid = get_id(e_res.get())
#             for v in rv.values(): v.set("—")
#             if not rid: return
#             _, r = run_query("""
#                 SELECT CONCAT(c.first_name,' ',c.last_name),
#                        v.model, v.category, v.vehicle_id,
#                        res.start_date, res.end_date, m.discount_rate
#                 FROM   RESERVATION res
#                 JOIN   CUSTOMER c    ON res.customer_id  = c.customer_id
#                 JOIN   VEHICLE v     ON res.vehicle_id   = v.vehicle_id
#                 JOIN   MEMBERSHIP m  ON c.membership_id  = m.membership_id
#                 WHERE  res.reservation_id = %s
#             """, (rid,))
#             if not r: return
#             cname, mdl, cat, vid, st, en, disc = r[0]
#             rate = get_daily_rate(cat)
#             eff  = rate * (1 - float(disc or 0) / 100)
#             rv["cust"].set(cname)
#             rv["veh"].set(f"#{vid} — {mdl} ({cat})")
#             rv["from"].set(str(st)[:10])
#             rv["to"].set(str(en)[:10])
#             rv["rate"].set(f"${eff:.2f}/day  (${rate} − {disc}% discount)")

#         e_res.bind("<<ComboboxSelected>>", on_res_select)

#         def do():
#             log_clear(log)
#             for v in vsv.values(): v.set("—")
#             res_id = get_id(e_res.get())
#             bid    = get_id(e_branch.get())
#             dt_raw = e_dt.get().strip()

#             pdt = validate_rental_start(log, res_id, bid, dt_raw)
#             if pdt is None: return

#             _, r = run_query(
#                 "SELECT vehicle_id, status, start_date, end_date "
#                 "FROM RESERVATION WHERE reservation_id = %s", (res_id,))
#             veh_id, res_st, res_start, res_end = r[0]

#             if res_st != "CONFIRMED":
#                 log_write(log, f"  ✗  Reservation #{res_id} is '{res_st}'. Must be CONFIRMED.", "err")
#                 return

#             _, vr = run_query(
#                 "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#             bef = vr[0][0] if vr else "?"
#             vsv["vid"].set(str(veh_id)); vsv["bef"].set(bef)

#             new_id = next_id("RENTAL", "rental_id", 7000, floor=7099)
#             ok, msg = run_write("""
#                 INSERT INTO RENTAL
#                     (rental_id, reservation_id, vehicle_id,
#                      pickup_branch_id, pickup_date, status)
#                 VALUES (%s,%s,%s,%s,%s,'ACTIVE')
#             """, (new_id, res_id, veh_id, bid, dt_raw))

#             if ok:
#                 _, vr2 = run_query(
#                     "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#                 aft = vr2[0][0] if vr2 else "?"
#                 vsv["aft"].set(aft)
#                 log_write(log, f"  ✔  Rental #{new_id} started!", "ok")
#                 log_write(log, f"     Res #{res_id}  |  Pickup: {dt_raw}", "ok")
#                 log_write(log, f"     [T3 ✔]  Vehicle #{veh_id}: {bef} → {aft}", "ok")
#                 ref_start()
#             else:
#                 if "TRIGGER BLOCKED" in msg:
#                     log_write(log, "  ══" * 22, "err")
#                     log_write(log, "  TRIGGER 2 FIRED ✔ — Customer docs invalid!", "err")
#                     log_write(log, f"  {msg}", "err")
#                     log_write(log, "  ══" * 22, "err")
#                 else:
#                     log_write(log, f"  ✗  {msg}", "err")

#         btn(fc, "▶  Start Rental", do,
#             color=C["accent2"], width=24).grid(
#             row=9, column=0, columnspan=2, pady=10)

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "CONFIRMED RESERVATIONS", font=FONT_HEAD,
#               fg=C["muted"]).pack(anchor="w")
#         rf, rt = make_tree(
#             rc, ["Res ID", "Cust ID", "Veh ID", "Start", "End", "Status"],
#             heights=18)
#         rf.pack(fill="both", expand=True, pady=4)

#         def ref_start():
#             c, r = run_query("""
#                 SELECT reservation_id, customer_id, vehicle_id,
#                        start_date, end_date, status
#                 FROM   RESERVATION WHERE status = 'CONFIRMED'
#                 ORDER  BY reservation_id""")
#             populate_tree(rt, c, r)

#         btn(rc, "🔄  Refresh", ref_start, width=14).pack(anchor="w")
#         ref_start()
#         return p

#     # ─────────────────────────────────────────
#     #  COMPLETE RENTAL
#     # ─────────────────────────────────────────
#     def _panel_end(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "COMPLETE A RENTAL  (RETURN)", bg=C["bg"]).pack(
#             anchor="w", pady=(0, 4))
#         label(p, "T4 flips vehicle → AVAILABLE",
#               fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

#         body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=20, pady=20)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         label(fc, "RETURN FORM", font=FONT_HEAD,
#               fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,4))
#         db_hint_row(fc, row=1)
#         e_rid    = combo_row(fc, "Active Rental",   2, load_rentals_active)
#         e_branch = combo_row(fc, "Return Branch",   3, load_branches)
#         e_dt     = form_row (fc, "Return DateTime", 4)
#         hint_row(fc, "YYYY-MM-DD HH:MM:SS   must be AFTER pickup time", 5)

#         _ctx = {}
#         pv = {k: tk.StringVar(value="—") for k in ["pu", "days", "rate", "est"]}
#         prev_f = tk.Frame(fc, bg=C["border"], padx=12, pady=8)
#         prev_f.grid(row=6, column=0, columnspan=2, sticky="ew", pady=6)
#         tk.Label(prev_f, text="CHARGE PREVIEW  (live — updates as you type)",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["border"]).pack(
#                  anchor="w", pady=(0, 4))
#         grid_f = tk.Frame(prev_f, bg=C["border"]); grid_f.pack(fill="x")
#         prev_fields = [
#             ("Pickup Date :",  pv["pu"],   C["text"],    0, 0),
#             ("Days Rented :",  pv["days"], C["text"],    1, 0),
#             ("Daily Rate :",   pv["rate"], C["text"],    2, 0),
#             ("Est. Total :",   pv["est"],  C["accent2"], 3, 0),
#         ]
#         for lbl_t, var, clr, pr, pc in prev_fields:
#             tk.Label(grid_f, text=lbl_t, font=FONT_SMALL, fg=C["muted"],
#                      bg=C["border"], width=14, anchor="w").grid(
#                      row=pr, column=pc, sticky="w")
#             tk.Label(grid_f, textvariable=var, font=FONT_MONO,
#                      fg=clr, bg=C["border"]).grid(
#                      row=pr, column=pc + 1, sticky="w", padx=(0, 16))

#         rv = {k: tk.StringVar(value="—") for k in ["pu", "days", "total", "vs"]}
#         info_block_grid(fc, 7, "COMPLETION RESULT  (T4)", [
#             ("Pickup Date  :", rv["pu"],    C["text"]),
#             ("Days Rented  :", rv["days"],  C["text"]),
#             ("Total Charged:", rv["total"], C["accent2"]),
#             ("Vehicle Now  :", rv["vs"],    C["accent2"]),
#         ])
#         log = log_box(fc, height=3)
#         log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(4, 0))

#         def load_ctx(e=None):
#             for v in pv.values(): v.set("—")
#             _ctx.clear()
#             rid = get_id(e_rid.get())
#             if not rid: return
#             _, r = run_query("""
#                 SELECT r.pickup_date, v.category, m.discount_rate
#                 FROM   RENTAL r
#                 JOIN   RESERVATION res ON r.reservation_id  = res.reservation_id
#                 JOIN   CUSTOMER c      ON res.customer_id   = c.customer_id
#                 JOIN   MEMBERSHIP m    ON c.membership_id   = m.membership_id
#                 JOIN   VEHICLE v       ON r.vehicle_id      = v.vehicle_id
#                 WHERE  r.rental_id = %s
#             """, (rid,))
#             if not r: return
#             pu_raw, cat, disc = r[0]
#             pdt = to_datetime(pu_raw)
#             if pdt is None: return
#             _ctx.update({"pdt": pdt, "cat": cat, "disc": disc})
#             pv["pu"].set(str(pdt)[:19])
#             _update_preview()

#         def _update_preview(e=None):
#             if not _ctx: return
#             dt_r = e_dt.get().strip()
#             if not dt_r: return
#             rdt = parse_datetime(dt_r)
#             if rdt is None or rdt <= _ctx["pdt"]: return
#             ch = calc_charge(_ctx["cat"], _ctx["disc"], _ctx["pdt"], rdt)
#             pv["days"].set(f"{ch['days']} day(s)")
#             pv["rate"].set(f"${ch['eff']:.2f}/day")
#             pv["est"].set(f"${ch['total']:.2f}")

#         e_rid.bind("<<ComboboxSelected>>", load_ctx)
#         e_dt.bind("<KeyRelease>", _update_preview)

#         def do():
#             log_clear(log)
#             for v in rv.values(): v.set("—")
#             rid    = get_id(e_rid.get())
#             bid    = get_id(e_branch.get())
#             dt_raw = e_dt.get().strip()

#             ret_dt, veh_id, pickup_dt = validate_rental_end(log, rid, bid, dt_raw)
#             if ret_dt is None: return

#             ch = calc_charge(_ctx["cat"], _ctx["disc"], pickup_dt, ret_dt)
#             total_amount = ch["total"]
#             days_rented = ch["days"]

#             rv["pu"].set(str(pickup_dt)[:19])
#             rv["days"].set(f"{days_rented} day(s)")

#             ok, msg = run_write("""
#                 UPDATE RENTAL SET status = 'COMPLETED',
#                        return_branch_id = %s, return_date = %s, total_amount = %s
#                 WHERE  rental_id = %s
#             """, (bid, dt_raw, total_amount, rid))

#             if ok:
#                 _, tr = run_query(
#                     "SELECT total_amount FROM RENTAL WHERE rental_id = %s", (rid,))
#                 total = tr[0][0] if tr else "?"
#                 _, vr = run_query(
#                     "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#                 vs = vr[0][0] if vr else "?"
#                 rv["total"].set(f"${total}")
#                 rv["vs"].set(vs)
#                 log_write(log, f"  ✔  Rental #{rid} completed! Total = ${total}", "ok")
#                 log_write(log, f"     [T4] Vehicle #{veh_id} → {vs}", "ok")
#                 log_write(log, "     → Go to Record Payment to settle the balance.", "info")
#                 ref_end()
#             else:
#                 log_write(log, f"  ✗  {msg}", "err")

#         btn(fc, "■  Complete Rental", do,
#             color=C["danger"], width=24).grid(
#             row=9, column=0, columnspan=2, pady=10)

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "ACTIVE RENTALS", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
#         rf, rt = make_tree(
#             rc, ["Rental ID", "Customer", "Model", "Pickup Date", "Status"],
#             heights=11)
#         rf.pack(fill="both", expand=True, pady=4)

#         label(rc, "RECENTLY COMPLETED", font=FONT_HEAD, fg=C["muted"]).pack(
#             anchor="w", pady=(6, 0))
#         rf2, rt2 = make_tree(
#             rc, ["Rental ID", "Customer", "Total $", "Return Date"], heights=8)
#         rf2.pack(fill="both", expand=True, pady=4)

#         def ref_end():
#             c, r = run_query("""
#                 SELECT r.rental_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        v.model, r.pickup_date, r.status
#                 FROM   RENTAL r
#                 JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
#                 JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
#                 JOIN   VEHICLE v ON r.vehicle_id = v.vehicle_id
#                 WHERE  r.status = 'ACTIVE' ORDER BY r.pickup_date DESC""")
#             populate_tree(rt, c, r)
#             c2, r2 = run_query("""
#                 SELECT r.rental_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        r.total_amount, r.return_date
#                 FROM   RENTAL r
#                 JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
#                 JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
#                 WHERE  r.status = 'COMPLETED'
#                 ORDER  BY r.rental_id DESC LIMIT 8""")
#             populate_tree(rt2, c2, r2)

#         btn(rc, "🔄  Refresh", ref_end, width=14).pack(anchor="w")
#         ref_end()
#         return p

#     # ─────────────────────────────────────────
#     #  RECORD PAYMENT
#     # ─────────────────────────────────────────
#     def _panel_payment(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "RECORD A PAYMENT", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
#         label(p, "Select a rental — balance is auto-calculated and pre-filled.",
#               fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

#         body = tk.Frame(p, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=20, pady=20)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         label(fc, "PAYMENT FORM", font=FONT_HEAD,
#               fg=C["accent"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,4))
#         db_hint_row(fc, row=1)
#         e_rid  = combo_row(fc, "Rental", 2, load_rentals_all)
#         res_var = tk.StringVar(value="")

#         bv = {k: tk.StringVar(value="—") for k in
#               ["cust", "res", "total", "paid", "bal", "status"]}
#         info_block_grid(fc, 3, "BALANCE SUMMARY", [
#             ("Customer      :", bv["cust"],   C["text"]),
#             ("Reservation   :", bv["res"],    C["accent"]),
#             ("Total Charged :", bv["total"],  C["text"]),
#             ("Already Paid  :", bv["paid"],   C["accent2"]),
#             ("Balance Owing :", bv["bal"],    C["warn"]),
#             ("Rental Status :", bv["status"], C["muted"]),
#         ])

#         e_amt  = form_row(fc, "Amount ($)", 4)
#         hint_row(fc, "Pre-filled from outstanding balance — edit for partial", 5)
#         e_type = static_combo_row(fc, "Payment Type", 6, PAYMENT_TYPES)
#         log = log_box(fc, height=6)
#         log.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

#         def on_sel(event=None):
#             log_clear(log)
#             for v in bv.values(): v.set("—")
#             res_var.set(""); e_amt.delete(0, "end")
#             rid = get_id(e_rid.get())
#             if not rid: return
#             _, r = run_query("""
#                 SELECT r.reservation_id, r.status,
#                        CONCAT(c.first_name,' ',c.last_name)
#                 FROM   RENTAL r
#                 JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
#                 JOIN   CUSTOMER c ON res.customer_id = c.customer_id
#                 WHERE  r.rental_id = %s
#             """, (rid,))
#             if not r:
#                 log_write(log, f"  ✗  Rental #{rid} not found.", "err"); return
#             res_id, rstatus, cname = r[0]
#             total, paid, bal = get_balance(rid)
#             bv["cust"].set(cname); bv["res"].set(f"#{res_id}")
#             bv["total"].set(f"${total:.2f}" if total > 0 else "— complete rental first")
#             bv["paid"].set(f"${paid:.2f}"); bv["bal"].set(f"${bal:.2f}")
#             bv["status"].set(rstatus); res_var.set(str(res_id))

#             if rstatus != "COMPLETED":
#                 e_amt.insert(0, "0.00")
#                 log_write(log, f"  ⚠  Rental is still {rstatus}. Complete it first for exact total.", "warn")
#             elif bal <= 0.005:
#                 e_amt.insert(0, "0.00")
#                 log_write(log, "  ✔  This rental is already fully paid.", "ok")
#             else:
#                 e_amt.insert(0, f"{bal:.2f}")
#                 if paid > 0:
#                     log_write(log, f"  ⚠  ${paid:.2f} already paid. Remaining balance: ${bal:.2f}", "warn")
#                 else:
#                     log_write(log, f"  ✔  Amount pre-filled: ${bal:.2f}", "ok")

#         e_rid.bind("<<ComboboxSelected>>", on_sel)

#         def do():
#             log_clear(log)
#             rid   = get_id(e_rid.get())
#             resid = res_var.get().strip()
#             amt   = e_amt.get().strip()
#             ptype = e_type.get().strip()
#             if not rid:   log_write(log, "  ✗  Please select a Rental.", "err");         return
#             if not resid: log_write(log, "  ✗  Select a rental first (reservation auto-fills).", "err"); return
#             if not amt:   log_write(log, "  ✗  Amount is required.", "err");              return
#             if not ptype: log_write(log, "  ✗  Please select a Payment Type.", "err");   return
#             try:
#                 amount = float(amt)
#             except ValueError:
#                 log_write(log, f"  ✗  '{amt}' is not a valid number.", "err"); return
#             if amount <= 0:
#                 log_write(log, "  ✗  Amount must be greater than $0.00.", "err"); return

#             total, paid, bal = get_balance(rid)
#             if total > 0 and amount > bal + 0.01:
#                 log_write(log, f"  ⚠  Paying ${amount:.2f} but balance is only ${bal:.2f}  (overpayment).", "warn")

#             new_id = next_id("PAYMENT", "payment_id", 8000)
#             ok, msg = run_write("""
#                 INSERT INTO PAYMENT
#                     (payment_id, rental_id, reservation_id,
#                      amount, payment_type, status)
#                 VALUES (%s,%s,%s,%s,%s,'COMPLETED')
#             """, (new_id, rid, resid, amount, ptype))

#             if ok:
#                 t2, p2, b2 = get_balance(rid)
#                 log_write(log, f"  ✔  Payment #{new_id} recorded!", "ok")
#                 log_write(log, f"     ${amount:,.2f} via {ptype}", "ok")
#                 log_write(log, f"     Balance: ${b2:.2f}",
#                     "ok" if b2 <= 0.005 else "warn")
#                 if b2 <= 0.005:
#                     log_write(log, "     ✔  FULLY PAID", "ok")
#                 ref_pay(); on_sel()
#             else:
#                 log_write(log, f"  ✗  {msg}", "err")

#         btn(fc, "$  Record Payment", do,
#             color=C["accent2"], width=24).grid(
#             row=8, column=0, columnspan=2, pady=10)

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "RECENT PAYMENTS", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
#         rf, rt = make_tree(
#             rc, ["Pay ID", "Rental", "Customer", "Amount", "Type", "Status"],
#             heights=10)
#         rf.pack(fill="both", expand=True, pady=4)

#         label(rc, "COMPLETED RENTALS — BALANCE VIEW",
#               font=FONT_HEAD, fg=C["muted"]).pack(anchor="w", pady=(6, 0))
#         bf, bt = make_tree(
#             rc, ["Rental", "Customer", "Total", "Paid", "Balance"],
#             heights=9)
#         bf.pack(fill="both", expand=True, pady=4)

#         def ref_pay():
#             c, r = run_query("""
#                 SELECT p.payment_id, p.rental_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        p.amount, p.payment_type, p.status
#                 FROM   PAYMENT p
#                 JOIN   RENTAL r2    ON p.rental_id        = r2.rental_id
#                 JOIN   RESERVATION s ON r2.reservation_id = s.reservation_id
#                 JOIN   CUSTOMER cu  ON s.customer_id      = cu.customer_id
#                 ORDER  BY p.payment_id DESC""")
#             populate_tree(rt, c, r)
#             _, r2 = run_query("""
#                 SELECT r.rental_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        r.total_amount,
#                        COALESCE(SUM(p.amount),0),
#                        GREATEST(r.total_amount - COALESCE(SUM(p.amount),0), 0)
#                 FROM   RENTAL r
#                 JOIN   RESERVATION s ON r.reservation_id  = s.reservation_id
#                 JOIN   CUSTOMER cu   ON s.customer_id     = cu.customer_id
#                 LEFT JOIN PAYMENT p  ON r.rental_id = p.rental_id
#                                      AND p.status = 'COMPLETED'
#                 WHERE  r.status = 'COMPLETED'
#                 GROUP  BY r.rental_id, cu.first_name, cu.last_name, r.total_amount
#                 ORDER  BY r.rental_id DESC LIMIT 15""")
#             populate_tree(bt, [], r2)
#             for ch in bt.get_children():
#                 vals = bt.item(ch)["values"]
#                 try:
#                     b = float(str(vals[4]).replace("NULL", "0"))
#                     bt.item(ch, tags=("paid",) if b <= 0.005 else ("owing",))
#                 except Exception:
#                     pass
#             bt.tag_configure("paid",  foreground=C["accent2"])
#             bt.tag_configure("owing", foreground=C["warn"])

#         btn(rc, "🔄  Refresh", ref_pay, width=14).pack(anchor="w")
#         ref_pay()
#         return p

#     # ─────────────────────────────────────────
#     #  ACTIVE RENTALS
#     # ─────────────────────────────────────────
#     def _panel_active(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "ACTIVE RENTALS", bg=C["bg"]).pack(anchor="w", pady=(0, 8))
#         tf, tree = make_tree(
#             p, ["Rental ID", "Customer", "Model", "Reg No",
#                 "Pickup Branch", "Pickup Date", "Status"],
#             heights=20)
#         tf.pack(fill="both", expand=True)
#         def ref():
#             c, r = run_query("""
#                 SELECT r.rental_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        v.model, v.registration_no,
#                        b.branch_name, r.pickup_date, r.status
#                 FROM   RENTAL r
#                 JOIN   RESERVATION res ON r.reservation_id = res.reservation_id
#                 JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
#                 JOIN   VEHICLE v ON r.vehicle_id = v.vehicle_id
#                 JOIN   BRANCH b ON r.pickup_branch_id = b.branch_id
#                 WHERE  r.status = 'ACTIVE' ORDER BY r.pickup_date DESC""")
#             populate_tree(tree, c, r)
#         btn(p, "🔄  Refresh", ref, width=16).pack(pady=8, anchor="w")
#         ref()
#         return p

#     # ─────────────────────────────────────────
#     #  REVENUE REPORT
#     # ─────────────────────────────────────────
#     def _panel_revenue(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "GLOBAL REVENUE REPORT", bg=C["bg"]).pack(anchor="w", pady=(0, 4))
#         label(p, "Revenue grouped by country of pickup branch",
#               fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))
#         top = tk.Frame(p, bg=C["bg"]); top.pack(fill="both", expand=True)
#         top.columnconfigure(0, weight=1); top.columnconfigure(1, weight=1)

#         lf = card_frame(top, padx=8, pady=8)
#         lf.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
#         label(lf, "BY COUNTRY", font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
#         cf, ct = make_tree(lf, ["Country", "Transactions", "Total Revenue ($)"], heights=12)
#         cf.pack(fill="both", expand=True, pady=4)

#         rf = card_frame(top, padx=8, pady=8)
#         rf.grid(row=0, column=1, sticky="nsew")
#         label(rf, "BY MEMBERSHIP TIER", font=FONT_HEAD, fg=C["accent"]).pack(anchor="w")
#         mf, mt = make_tree(rf, ["Tier", "Total Revenue ($)"], heights=12)
#         mf.pack(fill="both", expand=True, pady=4)

#         def ref():
#             c, r = run_query("""
#                 SELECT co.country_name, COUNT(p.payment_id),
#                        COALESCE(SUM(p.amount), 0)
#                 FROM   PAYMENT p
#                 JOIN   RENTAL r2 ON p.rental_id = r2.rental_id
#                 JOIN   BRANCH b  ON r2.pickup_branch_id = b.branch_id
#                 JOIN   CITY ci   ON b.city_id = ci.city_id
#                 JOIN   COUNTRY co ON ci.country_code = co.country_code
#                 GROUP  BY co.country_name ORDER BY 3 DESC""")
#             populate_tree(ct, c, r)
#             c2, r2 = run_query("""
#                 SELECT m.membership_type,
#                        COALESCE(SUM(p.amount), 0) AS revenue
#                 FROM   PAYMENT p
#                 JOIN   RESERVATION res ON p.reservation_id = res.reservation_id
#                 JOIN   CUSTOMER cu ON res.customer_id = cu.customer_id
#                 JOIN   MEMBERSHIP m ON cu.membership_id = m.membership_id
#                 GROUP  BY m.membership_type ORDER BY revenue DESC""")
#             populate_tree(mt, c2, r2)

#         btn(p, "🔄  Refresh", ref, width=16).pack(pady=8, anchor="w")
#         ref()
#         return p

#     # ─────────────────────────────────────────
#     #  TRIGGER DEMO PANEL
#     # ─────────────────────────────────────────
#     def _panel_triggers(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "⚡ TRIGGER DEMONSTRATION PANEL",
#                 fg=C["warn"], bg=C["bg"]).pack(anchor="w", pady=(0, 2))
#         label(p, "Live before/after proof for all trigger events — TA demo ready",
#               fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

#         s = ttk.Style()
#         s.configure("Trig.TNotebook", background=C["bg"], tabmargins=[2, 4, 2, 0])
#         s.configure("Trig.TNotebook.Tab",
#                     background=C["card"], foreground=C["text"],
#                     font=FONT_HEAD, padding=[14, 6])
#         s.map("Trig.TNotebook.Tab",
#               background=[("selected", C["warn"])],
#               foreground=[("selected", C["bg"])])

#         nb = ttk.Notebook(p, style="Trig.TNotebook")
#         nb.pack(fill="both", expand=True)
#         nb.add(self._t1(nb), text=" T1 — Overlap Block ")
#         nb.add(self._t2(nb), text=" T2 — Doc Check ")
#         nb.add(self._t3(nb), text=" T3 — Status -> RENTED ")
#         nb.add(self._t4(nb), text=" T4 — Status -> AVAILABLE ")
#         return p

#     def _t1(self, parent):
#         f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

#         hf = card_frame(f, padx=14, pady=10)
#         hf.pack(fill="x", pady=(0, 10))
#         tk.Label(hf, text="TRIGGER 1  —  BEFORE INSERT ON RESERVATION",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="LOGIC: Overlap is checked purely on DATES for the same vehicle — "
#                       "regardless of the vehicle's current status (AVAILABLE / RENTED). "
#                       "If any CONFIRMED reservation for that vehicle has dates that "
#                       "overlap the requested period, the INSERT is blocked.",
#                  font=FONT_SMALL, fg=C["text"], bg=C["card"],
#                  wraplength=700, justify="left").pack(anchor="w", pady=(4, 2))
#         tk.Label(hf,
#                  text="TO FAIL ▶  Pick any vehicle, enter dates that overlap an existing booking (see right table).",
#                  font=FONT_SMALL, fg=C["danger"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="TO PASS ▶  Enter dates with no overlap for the chosen vehicle.",
#                  font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="★ NOTE: Customer double-booking (same customer, overlapping dates) is also blocked at the app level.",
#                  font=FONT_SMALL, fg=C["accent"], bg=C["card"]).pack(anchor="w", pady=(4, 0))

#         body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=16, pady=16)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         db_hint_row(fc, row=0)
#         e_cust  = combo_row(fc, "Customer",   1, load_customers)
#         e_veh   = combo_row(fc, "Vehicle",    2, load_vehicles_all_no_status)
#         e_start = form_row (fc, "Start Date", 3)
#         hint_row(fc, "YYYY-MM-DD", 4)
#         e_end   = form_row (fc, "End Date",   5)
#         hint_row(fc, "YYYY-MM-DD   must be after Start Date", 6)
#         log = log_box(fc, height=11)
#         log.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

#         def do():
#             log_clear(log)
#             cid   = get_id(e_cust.get()); vid = get_id(e_veh.get())
#             st_r  = e_start.get().strip();   en_r = e_end.get().strip()
#             st, en = validate_reservation(log, cid, vid, st_r, en_r)
#             if st is None: return

#             conflicts = vehicle_overlap_check(vid, st_r, en_r)
#             if conflicts:
#                 log_write(log, f"  Pre-check: {len(conflicts)} vehicle conflict(s) for Vehicle #{vid}:", "warn")
#                 for row in conflicts:
#                     log_write(log,
#                         f"    Res #{row[0]}   "
#                         f"{str(row[1])[:10]} → {str(row[2])[:10]}", "warn")
#                 log_write(log, "  Sending to DB — Trigger 1 should block…", "warn")
#             else:
#                 log_write(log, "  Pre-check: No client-side conflict found. Sending to DB…", "info")

#             new_id = next_id("RESERVATION", "reservation_id", 6000)
#             log_write(log, f"  Attempting Reservation #{new_id}  ({st_r} → {en_r})…", "info")

#             ok, msg = run_write("""
#                 INSERT INTO RESERVATION
#                     (reservation_id, customer_id, vehicle_id,
#                      start_date, end_date, status)
#                 VALUES (%s,%s,%s,%s,%s,'CONFIRMED')
#             """, (new_id, cid, vid, st_r, en_r))

#             if ok:
#                 log_write(log, "", "info")
#                 log_write(log, "  ✔  PASS — No overlap. Reservation inserted.", "ok")
#                 log_write(log, f"     Reservation #{new_id} confirmed.", "ok")
#             else:
#                 if "TRIGGER BLOCKED" in msg:
#                     log_write(log, "", "err")
#                     log_write(log, "  ══" * 22, "err")
#                     log_write(log, "  TRIGGER 1 FIRED ✔", "err")
#                     log_write(log, "  Overlapping reservation BLOCKED at DB level!", "err")
#                     log_write(log, f"  {msg}", "err")
#                     log_write(log, "  ══" * 22, "err")
#                 else:
#                     log_write(log, f"  ✗  DB Error: {msg}", "err")
#             ref_t1()

#         btn(fc, "⚡ Run Trigger 1 Test", do,
#             color=C["warn"], width=24).grid(
#             row=8, column=0, columnspan=2, pady=10)

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "EXISTING RESERVATIONS  (check dates before testing)",
#               font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
#         label(rc,
#               "Look up the vehicle you choose and find dates that overlap → T1 will block.",
#               font=FONT_SMALL, fg=C["muted"]).pack(anchor="w", pady=(0, 4))
#         rf, rt = make_tree(
#             rc, ["Res ID", "Cust", "Veh", "Start", "End", "Status"],
#             heights=20)
#         rf.pack(fill="both", expand=True, pady=4)

#         def ref_t1():
#             c, r = run_query("""
#                 SELECT reservation_id, customer_id, vehicle_id,
#                        start_date, end_date, status
#                 FROM   RESERVATION ORDER BY vehicle_id, start_date""")
#             populate_tree(rt, c, r)

#         btn(rc, "🔄 Refresh", ref_t1, width=12).pack(anchor="w")
#         ref_t1()
#         return f

#     def _t2(self, parent):
#         f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

#         hf = card_frame(f, padx=14, pady=10)
#         hf.pack(fill="x", pady=(0, 10))
#         tk.Label(hf, text="TRIGGER 2  —  BEFORE INSERT ON RENTAL",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="LOGIC: The trigger checks whether the customer has AT LEAST ONE "
#                       "document with status='VERIFIED' AND expiry_date >= today. "
#                       "Even one expired/invalid document does NOT cause a block — "
#                       "only having ZERO valid documents causes the INSERT to be rejected.",
#                  font=FONT_SMALL, fg=C["text"], bg=C["card"],
#                  wraplength=700, justify="left").pack(anchor="w", pady=(4, 2))
#         tk.Label(hf,
#                  text="TO FAIL ▶  Customers 1003 (EXPIRED) | 1006 (PENDING) | 1007 (no doc)",
#                  font=FONT_SMALL, fg=C["danger"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="TO PASS ▶  Customers 1001, 1002, 1004, 1005, 1008, 1009",
#                  font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w")

#         body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=16, pady=16)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         db_hint_row(fc, row=0)
#         e_res    = combo_row(fc, "Reservation",  1, load_res_confirmed)
#         e_branch = combo_row(fc, "Pickup Branch", 2, load_branches)
#         e_dt     = form_row (fc, "Pickup DateTime", 3)
#         hint_row(fc, "YYYY-MM-DD HH:MM:SS   e.g. 2026-04-01 10:00:00", 4)

#         veh_var = tk.StringVar(value="— select a Reservation —")
#         tk.Label(fc, text="Vehicle (auto):", font=FONT_SMALL,
#                  fg=C["muted"], bg=C["card"]).grid(
#                  row=5, column=0, sticky="w", pady=4)
#         tk.Label(fc, textvariable=veh_var, font=FONT_HEAD,
#                  fg=C["accent"], bg=C["card"]).grid(
#                  row=5, column=1, sticky="w", pady=4)

#         log = log_box(fc, height=14)
#         log.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

#         def do():
#             log_clear(log); veh_var.set("…")
#             res_id = get_id(e_res.get())
#             bid    = get_id(e_branch.get())
#             dt_raw = e_dt.get().strip()

#             pdt = validate_rental_start(log, res_id, bid, dt_raw)
#             if pdt is None: return

#             _, r = run_query(
#                 "SELECT vehicle_id, status, customer_id, start_date, end_date "
#                 "FROM RESERVATION WHERE reservation_id = %s", (res_id,))
#             veh_id, rs, cid, res_st, res_en = r[0]
#             veh_var.set(f"#{veh_id}")

#             if rs != "CONFIRMED":
#                 log_write(log, f"  ✗  Reservation is '{rs}'. Must be CONFIRMED.", "err")
#                 return

#             has_valid, docs = customer_doc_status(cid)
#             log_write(log, f"  Customer #{cid} — Document check:", "heading")
#             log_write(log, "  " + "─" * 55, "info")
#             if docs:
#                 for d_type, d_status, d_exp in docs:
#                     is_valid = (d_status == "VERIFIED")
#                     tag  = "ok" if is_valid else "err"
#                     mark = "✔ VALID" if is_valid else "✗ INVALID"
#                     log_write(log,
#                         f"    {d_type:<28}  {d_status:<12}  "
#                         f"exp:{str(d_exp)[:10]}   [{mark}]", tag)
#             else:
#                 log_write(log, "    (no documents on file)  → WILL BE BLOCKED", "err")
#             log_write(log, "  " + "─" * 55, "info")
#             if has_valid:
#                 log_write(log,
#                     "  ✔ Pre-check: At least one VERIFIED, unexpired doc found. "
#                     "Expecting PASS.", "ok")
#             else:
#                 log_write(log,
#                     "  ✗ Pre-check: NO valid document found. "
#                     "Trigger 2 WILL fire.", "warn")

#             new_id = next_id("RENTAL", "rental_id", 7000, floor=7099)
#             log_write(log, f"\n  Sending INSERT for Rental #{new_id}…", "info")

#             ok, msg = run_write("""
#                 INSERT INTO RENTAL
#                     (rental_id, reservation_id, vehicle_id,
#                      pickup_branch_id, pickup_date, status)
#                 VALUES (%s,%s,%s,%s,%s,'ACTIVE')
#             """, (new_id, res_id, veh_id, bid, dt_raw))

#             if ok:
#                 _, vr = run_query(
#                     "SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#                 log_write(log, "  ✔  PASS — Rental started. Valid document confirmed.", "ok")
#                 log_write(log, f"     Rental #{new_id} is now ACTIVE.", "ok")
#             else:
#                 if "TRIGGER BLOCKED" in msg:
#                     log_write(log, "  ══" * 22, "err")
#                     log_write(log, "  TRIGGER 2 FIRED ✔", "err")
#                     log_write(log, "  Rental BLOCKED — no valid document!", "err")
#                     log_write(log, f"  {msg}", "err")
#                     log_write(log, "  ══" * 22, "err")
#                 else:
#                     log_write(log, f"  ✗  {msg}", "err")

#         btn(fc, "⚡ Run Trigger 2 Test", do,
#             color=C["warn"], width=24).grid(
#             row=7, column=0, columnspan=2, pady=10)

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "ALL CUSTOMER DOCUMENTS  (reference)",
#               font=FONT_HEAD, fg=C["muted"]).pack(anchor="w")
#         label(rc,
#               "Green = VERIFIED & non-expired (counts as valid)   "
#               "Red = expired / rejected / pending",
#               font=FONT_SMALL, fg=C["muted"]).pack(anchor="w", pady=(0, 4))
#         df, dt2 = make_tree(
#             rc, ["Cust ID", "Name", "Doc Type", "Status", "Expiry"],
#             heights=20)
#         df.pack(fill="both", expand=True, pady=4)

#         def ref_t2():
#             c, r = run_query("""
#                 SELECT cu.customer_id,
#                        CONCAT(cu.first_name,' ',cu.last_name),
#                        d.document_type, d.status, d.expiry_date
#                 FROM   CUSTOMER cu
#                 LEFT JOIN DOCUMENT d ON cu.customer_id = d.customer_id
#                 ORDER  BY cu.customer_id""")
#             populate_tree(dt2, c, r)
#             for ch in dt2.get_children():
#                 vals = dt2.item(ch)["values"]
#                 st = vals[3] if len(vals) > 3 else ""
#                 if st == "VERIFIED":
#                     dt2.item(ch, tags=("ok",))
#                 elif st in ("EXPIRED", "REJECTED"):
#                     dt2.item(ch, tags=("bad",))
#                 else:
#                     dt2.item(ch, tags=("wrn",))
#             dt2.tag_configure("ok",  foreground=C["accent2"])
#             dt2.tag_configure("bad", foreground=C["danger"])
#             dt2.tag_configure("wrn", foreground=C["warn"])

#         btn(rc, "🔄 Refresh", ref_t2, width=12).pack(anchor="w")
#         ref_t2()
#         return f

#     def _t3(self, parent):
#         outer = tk.Frame(parent, bg=C["bg"])

#         hf = tk.Frame(outer, bg=C["card"], padx=14, pady=10)
#         hf.pack(fill="x", padx=16, pady=(12, 8))
#         tk.Label(hf, text="TRIGGER 3  —  AFTER INSERT ON RENTAL",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="LOGIC: Automatically updates vehicle.status to 'RENTED' when a new rental starts.",
#                  font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w", pady=(4, 0))
#         tk.Label(hf,
#                  text="TO TEST ▶  Fill the Pickup form below and click Start Rental. Watch the tracker update.",
#                  font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

#         body = tk.Frame(outer, bg=C["bg"])
#         body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         left_outer = tk.Frame(body, bg=C["bg"])
#         left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         left = make_scrollable(left_outer, bg=C["bg"])

#         tracker = tk.Frame(left, bg=C["border"], padx=14, pady=12)
#         tracker.pack(fill="x", pady=(0, 10))
#         tk.Label(tracker, text="◉  VEHICLE STATUS TRACKER",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["border"]).pack(anchor="w")

#         vl_var  = tk.StringVar(value="Vehicle : —")
#         bef_var = tk.StringVar(value="BEFORE  : —")
#         aft_var = tk.StringVar(value="AFTER   : —")
#         for var, fg_clr in [(vl_var, C["accent"]), (bef_var, C["warn"]), (aft_var, C["accent2"])]:
#             tk.Label(tracker, textvariable=var, font=("Courier New", 12, "bold"),
#                      fg=fg_clr, bg=C["border"]).pack(anchor="w", pady=2)

#         fa = tk.Frame(left, bg=C["card"], padx=14, pady=12)
#         fa.pack(fill="x", pady=(4, 6))
#         tk.Label(fa, text="▶  TRIGGER 3 — Start Rental (Pickup)",
#                  font=FONT_HEAD, fg=C["accent"], bg=C["card"]).grid(
#                  row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
#         db_hint_row(fa, row=1)
#         e3_res    = combo_row(fa, "Reservation",   2, load_res_confirmed)
#         e3_branch = combo_row(fa, "Pickup Branch", 3, load_branches)
#         e3_dt     = form_row (fa, "Pickup DateTime", 4)
#         hint_row(fa, "YYYY-MM-DD HH:MM:SS", 5)
#         log3 = log_box(fa, height=8)
#         log3.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

#         def do_3():
#             log_clear(log3); bef_var.set("BEFORE  : —"); aft_var.set("AFTER   : —"); vl_var.set("Vehicle : —")
#             res_id = get_id(e3_res.get()); bid = get_id(e3_branch.get()); dt_raw = e3_dt.get().strip()

#             pdt = validate_rental_start(log3, res_id, bid, dt_raw)
#             if pdt is None: return

#             _, r = run_query("SELECT vehicle_id, status FROM RESERVATION WHERE reservation_id = %s", (res_id,))
#             veh_id, rs = r[0]

#             if rs != "CONFIRMED":
#                 log_write(log3, f"  ✗  Reservation is '{rs}'. Must be CONFIRMED.", "err")
#                 return

#             _, vr = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#             bef = vr[0][0] if vr else "?"
#             vl_var.set(f"Vehicle : #{veh_id}"); bef_var.set(f"BEFORE  : {bef}")

#             new_id = next_id("RENTAL", "rental_id", 7000, floor=7099)
#             ok, msg = run_write("""
#                 INSERT INTO RENTAL (rental_id, reservation_id, vehicle_id, pickup_branch_id, pickup_date, status)
#                 VALUES (%s,%s,%s,%s,%s,'ACTIVE')
#             """, (new_id, res_id, veh_id, bid, dt_raw))

#             if ok:
#                 _, vr2 = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#                 aft = vr2[0][0] if vr2 else "?"
#                 aft_var.set(f"AFTER   : {aft}")
#                 log_write(log3, f"  ✔  [T3 ✔]  Vehicle #{veh_id}:  {bef}  →  {aft}", "ok")
#                 log_write(log3, f"     Rental #{new_id} is now ACTIVE.", "ok")
                
#                 # AUTO-REFRESH LOGIC
#                 e3_res.set('')
#                 e3_dt.delete(0, 'end')
#                 e3_res['values'] = load_res_confirmed()
#                 ref_t3()
#             else:
#                 log_write(log3, f"  ✗  {msg}", "err")

#         btn(fa, "▶  Test Trigger 3", do_3, color=C["accent"], width=24).grid(row=7, column=0, columnspan=2, pady=(10, 2))

#         # ── Right column: reference tables ───────────────────────────────
#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")

#         # Header frame to hold Title (Left) and Refresh Button (Right)
#         header_f = tk.Frame(rc, bg=C["card"])
#         header_f.pack(fill="x", pady=(0, 4))
        
#         label(header_f, "VEHICLE STATUS  (live)", font=FONT_HEAD, fg=C["muted"]).pack(side="left")

#         def ref_t3():
#             c, r = run_query("SELECT vehicle_id, model, category, status FROM VEHICLE ORDER BY vehicle_id")
#             populate_tree(vt, c, r)
#             for ch in vt.get_children():
#                 st = vt.item(ch)["values"][3]
#                 vt.item(ch, tags=("rented",) if st == "RENTED" else ("avail",))
#             vt.tag_configure("rented", foreground=C["danger"])
#             vt.tag_configure("avail",  foreground=C["accent2"])

#         # Button packed to the right of the title!
#         btn(header_f, "🔄 Refresh", ref_t3, width=12).pack(side="right")

#         vf, vt = make_tree(rc, ["ID", "Model", "Category", "Status"], heights=20)
#         vf.pack(fill="both", expand=True)

#         ref_t3()
#         return outer

#     def _t4(self, parent):
#         outer = tk.Frame(parent, bg=C["bg"])

#         hf = tk.Frame(outer, bg=C["card"], padx=14, pady=10)
#         hf.pack(fill="x", padx=16, pady=(12, 8))
#         tk.Label(hf, text="TRIGGER 4  —  AFTER UPDATE ON RENTAL (status → 'COMPLETED')",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf,
#                  text="LOGIC: Automatically updates vehicle.status to 'AVAILABLE' when a rental is completed.",
#                  font=FONT_SMALL, fg=C["accent2"], bg=C["card"]).pack(anchor="w", pady=(4, 0))
#         tk.Label(hf,
#                  text="TO TEST ▶  Select an active rental, enter the return datetime, and click Complete Rental.",
#                  font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

#         body = tk.Frame(outer, bg=C["bg"])
#         body.pack(fill="both", expand=True, padx=16, pady=(0, 12))
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         left_outer = tk.Frame(body, bg=C["bg"])
#         left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         left = make_scrollable(left_outer, bg=C["bg"])

#         tracker = tk.Frame(left, bg=C["border"], padx=14, pady=12)
#         tracker.pack(fill="x", pady=(0, 10))
#         tk.Label(tracker, text="◉  VEHICLE STATUS TRACKER", font=FONT_HEAD, fg=C["warn"], bg=C["border"]).pack(anchor="w")

#         vl_var  = tk.StringVar(value="Vehicle : —")
#         bef_var = tk.StringVar(value="BEFORE  : —")
#         aft_var = tk.StringVar(value="AFTER   : —")
#         for var, fg_clr in [(vl_var, C["accent"]), (bef_var, C["warn"]), (aft_var, C["accent2"])]:
#             tk.Label(tracker, textvariable=var, font=("Courier New", 12, "bold"), fg=fg_clr, bg=C["border"]).pack(anchor="w", pady=2)

#         fb = tk.Frame(left, bg=C["card"], padx=14, pady=12)
#         fb.pack(fill="x", pady=(4, 6))
#         tk.Label(fb, text="■  TRIGGER 4 — Complete Rental (Return)", font=FONT_HEAD, fg=C["accent"], bg=C["card"]).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
#         db_hint_row(fb, row=1)
#         e4_rid    = combo_row(fb, "Active Rental",   2, load_rentals_active)
#         e4_branch = combo_row(fb, "Return Branch",   3, load_branches)
#         e4_dt     = form_row (fb, "Return DateTime", 4)
#         hint_row(fb, "YYYY-MM-DD HH:MM:SS", 5)
#         log4 = log_box(fb, height=8)
#         log4.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(6, 0))

#         _ctx = {}

#         def load_ctx(e=None):
#             _ctx.clear()
#             rid = get_id(e4_rid.get())
#             if not rid: return
#             _, r = run_query("""
#                 SELECT r.pickup_date, v.category, m.discount_rate
#                 FROM   RENTAL r
#                 JOIN   RESERVATION res ON r.reservation_id  = res.reservation_id
#                 JOIN   CUSTOMER c      ON res.customer_id   = c.customer_id
#                 JOIN   MEMBERSHIP m    ON c.membership_id   = m.membership_id
#                 JOIN   VEHICLE v       ON r.vehicle_id      = v.vehicle_id
#                 WHERE  r.rental_id = %s
#             """, (rid,))
#             if not r: return
#             pdt = to_datetime(r[0][0])
#             _ctx.update({"pdt": pdt, "cat": r[0][1], "disc": r[0][2]})

#         e4_rid.bind("<<ComboboxSelected>>", load_ctx)

#         def do_4():
#             log_clear(log4); bef_var.set("BEFORE  : —"); aft_var.set("AFTER   : —"); vl_var.set("Vehicle : —")
#             rid = get_id(e4_rid.get()); bid = get_id(e4_branch.get()); dt_raw = e4_dt.get().strip()

#             ret_dt, veh_id, pickup_dt = validate_rental_end(log4, rid, bid, dt_raw)
#             if ret_dt is None: return

#             _, vr = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#             bef = vr[0][0] if vr else "?"
#             bef_var.set(f"BEFORE  : {bef}"); vl_var.set(f"Vehicle : #{veh_id}")

#             ch = calc_charge(_ctx["cat"], _ctx["disc"], pickup_dt, ret_dt)
#             total_amt = ch["total"]

#             ok, msg = run_write("""
#                 UPDATE RENTAL SET status = 'COMPLETED',
#                        return_branch_id = %s, return_date = %s, total_amount = %s
#                 WHERE  rental_id = %s
#             """, (bid, dt_raw, total_amt, rid))

#             if ok:
#                 _, vr2 = run_query("SELECT status FROM VEHICLE WHERE vehicle_id = %s", (veh_id,))
#                 aft = vr2[0][0] if vr2 else "?"
#                 aft_var.set(f"AFTER   : {aft}")
#                 log_write(log4, f"  ✔  [T4 ✔]  Vehicle #{veh_id}:  {bef}  →  {aft}", "ok")
#                 log_write(log4, f"     Rental #{rid} is now COMPLETED. (Total: ${total_amt:.2f})", "ok")
                
#                 # AUTO-REFRESH LOGIC
#                 e4_rid.set('')
#                 e4_dt.delete(0, 'end')
#                 e4_rid['values'] = load_rentals_active()
#                 ref_t4()
#             else:
#                 log_write(log4, f"  ✗  {msg}", "err")

#         btn(fb, "■  Test Trigger 4", do_4, color=C["danger"], width=24).grid(row=7, column=0, columnspan=2, pady=(10, 2))

#         # ── Right column: reference tables ───────────────────────────────
#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")

#         # Header frame to hold Title (Left) and Refresh Button (Right)
#         header_f = tk.Frame(rc, bg=C["card"])
#         header_f.pack(fill="x", pady=(0, 4))
        
#         label(header_f, "VEHICLE STATUS  (live)", font=FONT_HEAD, fg=C["muted"]).pack(side="left")

#         def ref_t4():
#             c, r = run_query("SELECT vehicle_id, model, category, status FROM VEHICLE ORDER BY vehicle_id")
#             populate_tree(vt, c, r)
#             for ch in vt.get_children():
#                 st = vt.item(ch)["values"][3]
#                 vt.item(ch, tags=("rented",) if st == "RENTED" else ("avail",))
#             vt.tag_configure("rented", foreground=C["danger"])
#             vt.tag_configure("avail",  foreground=C["accent2"])

#         # Button packed to the right of the title!
#         btn(header_f, "🔄 Refresh", ref_t4, width=12).pack(side="right")

#         vf, vt = make_tree(rc, ["ID", "Model", "Category", "Status"], heights=20)
#         vf.pack(fill="both", expand=True)

#         ref_t4()
#         return outer

#     # ─────────────────────────────────────────
#     #  TASK 6: TRANSACTIONS DEMO PANEL
#     # ─────────────────────────────────────────
#     def _panel_transactions(self):
#         p = tk.Frame(self.container, bg=C["bg"])
#         heading(p, "🔄 TASK 6: TRANSACTIONS DEMO",
#                 fg=C["accent2"], bg=C["bg"]).pack(anchor="w", pady=(0, 2))
#         label(p, "Demonstrate Atomicity (Commit/Rollback) and Isolation (Concurrency & Locks)",
#               fg=C["muted"], bg=C["bg"]).pack(anchor="w", pady=(0, 10))

#         s = ttk.Style()
#         s.configure("Tx.TNotebook", background=C["bg"], tabmargins=[2, 4, 2, 0])
#         s.configure("Tx.TNotebook.Tab",
#                     background=C["card"], foreground=C["text"],
#                     font=FONT_HEAD, padding=[14, 6])
#         s.map("Tx.TNotebook.Tab",
#               background=[("selected", C["accent2"])],
#               foreground=[("selected", C["bg"])])

#         nb = ttk.Notebook(p, style="Tx.TNotebook")
#         nb.pack(fill="both", expand=True)
#         nb.add(self._tx_atomicity(nb), text=" Part A: Atomicity (Commit/Rollback) ")
#         nb.add(self._tx_isolation(nb), text=" Part B: Isolation (Concurrency Conflict) ")
#         return p

#     def _tx_atomicity(self, parent):
#         f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

#         hf = card_frame(f, padx=14, pady=10)
#         hf.pack(fill="x", pady=(0, 10))
#         tk.Label(hf, text="SCENARIO: A customer makes a Reservation AND pays a Deposit in a single Transaction.",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf, text="SUCCESS: The DB successfully saves BOTH the Reservation and the Payment (COMMIT).\n"
#                           "FAILURE: The Payment fails midway. The DB reverses the Reservation to prevent orphaned data (ROLLBACK).",
#                  font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

#         body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2)

#         fc = card_frame(body, padx=16, pady=16)
#         fc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         e_cust = combo_row(fc, "Customer", 0, load_customers)
#         e_veh  = combo_row(fc, "Vehicle", 1, load_vehicles_available)
#         e_st   = form_row(fc, "Start Date", 2); e_st.insert(0, "2026-12-01")
#         e_en   = form_row(fc, "End Date", 3); e_en.insert(0, "2026-12-05")
        
#         tk.Frame(fc, bg=C["border"], height=1).grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
#         e_amt  = form_row(fc, "Deposit Amount ($)", 5); e_amt.insert(0, "100.00")
        
#         log = log_box(fc, height=10)
#         log.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(15, 0))

#         def execute_tx(simulate_fail=False):
#             log_clear(log)
#             cid = get_id(e_cust.get()); vid = get_id(e_veh.get())
#             st = e_st.get().strip(); en = e_en.get().strip()
#             amt = e_amt.get().strip()
            
#             if not all([cid, vid, st, en, amt]):
#                 log_write(log, "  ✗  All fields are required.", "err"); return

#             new_res_id = next_id("RESERVATION", "reservation_id", 6600)
#             new_pay_id = next_id("PAYMENT", "payment_id", 8600)

#             conn = get_conn()
#             if not conn: return

#             try:
#                 # 1. START TRANSACTION
#                 conn.start_transaction()
#                 log_write(log, "▶ TRANSACTION STARTED", "warn")
                
#                 cur = conn.cursor()
                
#                 # 2. INSERT RESERVATION
#                 log_write(log, f"  [Step 1] Attempting to INSERT Reservation #{new_res_id}...", "info")
#                 cur.execute("""
#                     INSERT INTO RESERVATION (reservation_id, customer_id, vehicle_id, start_date, end_date, status)
#                     VALUES (%s, %s, %s, %s, %s, 'CONFIRMED')
#                 """, (new_res_id, cid, vid, st, en))
#                 log_write(log, "  ✔ Reservation inserted into DB memory.", "ok")
                
#                 # SIMULATE ERROR
#                 if simulate_fail:
#                     log_write(log, f"  [Step 2] Attempting to process Payment of ${amt}...", "info")
#                     log_write(log, "  💥 FATAL ERROR: Payment Gateway Timeout!", "err")
#                     raise Exception("Payment Failed")
                
#                 # 3. INSERT PAYMENT
#                 log_write(log, f"  [Step 2] Attempting to process Payment of ${amt}...", "info")
#                 cur.execute("""
#                     INSERT INTO PAYMENT (payment_id, reservation_id, amount, payment_type, status)
#                     VALUES (%s, %s, %s, 'Credit Card', 'COMPLETED')
#                 """, (new_pay_id, new_res_id, float(amt)))
#                 log_write(log, "  ✔ Payment processed successfully.", "ok")

#                 # 4. COMMIT
#                 conn.commit()
#                 log_write(log, "\n✔ TRANSACTION COMMITTED SUCCESSFULLY!", "accent2")
                
#             except Exception as e:
#                 # 5. ROLLBACK
#                 conn.rollback()
#                 log_write(log, f"\n✗ TRANSACTION ROLLED BACK DUE TO ERROR.", "err")
#                 log_write(log, "  The Reservation was NOT saved to the database.", "err")
#             finally:
#                 cur.close(); conn.close()
#                 ref_tables()

#         btn(fc, "1. Execute & COMMIT (Success)", lambda: execute_tx(False), color=C["accent2"], width=30).grid(row=6, column=0, columnspan=2, pady=(10, 2))
#         btn(fc, "2. Execute & ROLLBACK (Fail)", lambda: execute_tx(True), color=C["danger"], width=30).grid(row=7, column=0, columnspan=2, pady=(2, 10))

#         # ── Right column: reference tables ───────────────────────────────
#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
        
#         # Header frame to hold Title and Refresh Button
#         header_f = tk.Frame(rc, bg=C["card"])
#         header_f.pack(fill="x", pady=(0, 4))
#         label(header_f, "RESERVATIONS TABLE", font=FONT_HEAD, fg=C["muted"]).pack(side="left")

#         def ref_tables():
#             c1, r1 = run_query("SELECT reservation_id, customer_id, vehicle_id, start_date, end_date FROM RESERVATION ORDER BY reservation_id DESC LIMIT 10")
#             populate_tree(rt, c1, r1)
#             c2, r2 = run_query("SELECT payment_id, reservation_id, amount, payment_type FROM PAYMENT ORDER BY payment_id DESC LIMIT 10")
#             populate_tree(pt, c2, r2)
            
#         # Refresh button locked to the top right!
#         btn(header_f, "🔄 Refresh", ref_tables, width=12).pack(side="right")

#         # Reduced heights slightly so it fits on screen
#         rf, rt = make_tree(rc, ["Res ID", "Cust", "Veh", "Start", "End"], heights=8)
#         rf.pack(fill="both", expand=True, pady=4)
        
#         label(rc, "PAYMENTS TABLE", font=FONT_HEAD, fg=C["muted"]).pack(anchor="w", pady=(10,0))
#         pf, pt = make_tree(rc, ["Pay ID", "Res ID", "Amount", "Type"], heights=8)
#         pf.pack(fill="both", expand=True, pady=4)

#         ref_tables()
#         return f

#     def _tx_isolation(self, parent):
#         f = tk.Frame(parent, bg=C["bg"], padx=16, pady=12)

#         hf = card_frame(f, padx=14, pady=10)
#         hf.pack(fill="x", pady=(0, 10))
#         tk.Label(hf, text="SCENARIO: Two employees try to update the EXACT SAME vehicle simultaneously.",
#                  font=FONT_HEAD, fg=C["warn"], bg=C["card"]).pack(anchor="w")
#         tk.Label(hf, text="ISOLATION: User 1 starts a transaction and modifies Vehicle 501. Before User 1 commits, User 2 tries to modify Vehicle 501.\n"
#                           "Because of InnoDB Row-Level Locking, User 2 is BLOCKED and must wait, preventing data corruption.",
#                  font=FONT_SMALL, fg=C["text"], bg=C["card"], justify="left").pack(anchor="w", pady=(4, 0))

#         body = tk.Frame(f, bg=C["bg"]); body.pack(fill="both", expand=True)
#         body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=1)

#         lc = card_frame(body, padx=16, pady=16)
#         lc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
#         e_veh = combo_row(lc, "Target Vehicle", 0, load_vehicles_all_no_status)
        
#         log = log_box(lc, height=18)
#         log.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0))

#         def execute_concurrency():
#             log_clear(log)
#             vid = get_id(e_veh.get())
#             if not vid:
#                 log_write(log, "  ✗  Select a vehicle first.", "err"); return

#             # Open two distinct connections to simulate two different users
#             conn1 = get_conn()
#             conn2 = get_conn()
            
#             if not conn1 or not conn2: return

#             try:
#                 cur1 = conn1.cursor()
#                 cur2 = conn2.cursor()

#                 # --- USER 1 ---
#                 log_write(log, "▶ USER 1: Starts Transaction...", "accent2")
#                 conn1.start_transaction()
                
#                 log_write(log, f"▶ USER 1: Updating Vehicle #{vid} to 'RENTED'...", "accent2")
#                 cur1.execute("UPDATE VEHICLE SET status = 'RENTED' WHERE vehicle_id = %s", (vid,))
#                 log_write(log, "▶ USER 1: Update executed. (Not committed yet). Row is now LOCKED.", "warn")
                
#                 # Force UI to update immediately before blocking
#                 self.update() 

#                 # --- USER 2 ---
#                 log_write(log, "\n▶ USER 2: Starts Transaction...", "accent")
#                 conn2.start_transaction()
                
#                 # Set a short timeout for the demo so we don't freeze the UI forever
#                 cur2.execute("SET SESSION innodb_lock_wait_timeout = 2")
                
#                 log_write(log, f"▶ USER 2: Attempting to update Vehicle #{vid} to 'UNDER_MAINTENANCE'...", "accent")
#                 log_write(log, "▶ USER 2: WAITING for lock... (UI will pause for 2 seconds)", "muted")
#                 self.update()

#                 try:
#                     # This will block because User 1 holds the lock!
#                     cur2.execute("UPDATE VEHICLE SET status = 'UNDER_MAINTENANCE' WHERE vehicle_id = %s", (vid,))
#                 except mysql.connector.Error as err:
#                     log_write(log, f"\n💥 USER 2 CRASHED: {err}", "err")
#                     log_write(log, "  Proof: The Database prevented concurrent modification!", "err")

#                 # --- CLEANUP ---
#                 log_write(log, "\n▶ USER 1: Rolling back transaction to release locks and clean up DB...", "info")
#                 conn1.rollback()
#                 log_write(log, "✔ Demo finished. Database is safe.", "ok")

#             except Exception as e:
#                 log_write(log, f"System Error: {e}", "err")
#             finally:
#                 if conn1.is_connected():
#                     cur1.close(); conn1.close()
#                 if conn2.is_connected():
#                     cur2.close(); conn2.close()

#         btn(lc, "⚡ Simulate Concurrent Conflict", execute_concurrency, color=C["warn"], width=30).grid(row=1, column=0, columnspan=2, pady=(10, 2))

#         rc = card_frame(body, padx=8, pady=8)
#         rc.grid(row=0, column=1, sticky="nsew")
#         label(rc, "SQL EXPLANATION", font=FONT_HEAD, fg=C["accent2"]).pack(anchor="w")
        
#         sql_text = """
# -- Connection 1 (User 1)
# START TRANSACTION;
# UPDATE vehicle 
# SET status = 'RENTED' 
# WHERE vehicle_id = 501;

# -- Connection 2 (User 2) runs simultaneously:
# START TRANSACTION;
# -- Tries to update the same row
# UPDATE vehicle 
# SET status = 'UNDER_MAINTENANCE' 
# WHERE vehicle_id = 501;
# -- ❌ BLOCKS until Connection 1 finishes, 
# -- or throws 'Lock wait timeout exceeded'

# -- Connection 1 decides to Rollback
# ROLLBACK; 
#         """
#         stb = scrolledtext.ScrolledText(rc, height=20, font=FONT_MONO, bg=C["bg"], fg=C["accent2"], relief="flat")
#         stb.pack(fill="both", expand=True, pady=4)
#         stb.insert("1.0", sql_text)
#         stb.config(state="disabled")

#         return f


# # ─────────────────────────────────────────────
# #  ENTRY POINT
# # ─────────────────────────────────────────────
# if __name__ == "__main__":
#     app = CarRentalApp()
#     app.mainloop()