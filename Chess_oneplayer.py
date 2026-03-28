import pygame
import sys
import threading
import copy

# ── Bootstrap: get display size before creating window ─────────────────────────
pygame.init()
info        = pygame.display.Info()
WIN_W       = info.current_w
WIN_H       = info.current_h

# ── Layout (computed from screen size) ─────────────────────────────────────────
SIDEBAR_W   = max(300, WIN_W // 4)
PADDING     = max(16, WIN_W // 80)
STATUS_H    = 48

BOARD_MAX   = min(WIN_H - STATUS_H - PADDING * 2, WIN_W - SIDEBAR_W - PADDING * 3)
BOARD_SIZE  = (BOARD_MAX // 8) * 8          # keep multiple of 8
CELL        = BOARD_SIZE // 8

BOARD_X     = PADDING
BOARD_Y     = STATUS_H + (WIN_H - STATUS_H - BOARD_SIZE) // 2

SIDE_X      = BOARD_X + BOARD_SIZE + PADDING * 2
SIDE_Y      = STATUS_H + PADDING // 2
SIDE_H      = WIN_H - SIDE_Y - PADDING

FILES = 'abcdefgh'

# ── Colours ────────────────────────────────────────────────────────────────────
LIGHT      = (240, 217, 181)
DARK       = (181, 136,  99)
BG         = ( 20,  16,  12)
PANEL_BG   = ( 30,  24,  18)
PANEL_LINE = ( 55,  44,  33)
HIGHLIGHT  = (205, 210,  65, 170)
SELECTED   = (100, 180,  50, 200)
CHECK_CLR  = (220,  60,  60, 180)
MOVE_DOT   = ( 80, 140,  40, 160)
CPU_MOVE   = ( 80, 160, 220, 150)
BORDER     = ( 90,  65,  40)
GOLD       = (212, 175,  55)
DIM        = (110,  90,  65)
W_TXT      = (230, 220, 205)
B_TXT      = ( 28,  22,  16)   # near-black for white side score text
CPU_TXT    = (240, 235, 228)   # near-white for cpu side score text

FPS        = 60
CPU_COLOR  = 'b'
HUMAN_COLOR= 'w'

# Point values per spec
PIECE_SCORE = {'P':1,'N':3,'B':3,'R':4,'Q':9,'K':0}
# Descending order for captures display
CAP_ORDER   = ['Q','R','B','N','P']

UNICODE_PIECES = {
    ('K','w'):'♔',('Q','w'):'♕',('R','w'):'♖',
    ('B','w'):'♗',('N','w'):'♘',('P','w'):'♙',
    ('K','b'):'♚',('Q','b'):'♛',('R','b'):'♜',
    ('B','b'):'♝',('N','b'):'♞',('P','b'):'♟',
}

# ── Board ──────────────────────────────────────────────────────────────────────
def init_board():
    back  = ['R','N','B','Q','K','B','N','R']
    board = [[None]*8 for _ in range(8)]
    for c,p in enumerate(back):
        board[0][c] = (p,'b')
        board[7][c] = (p,'w')
    for c in range(8):
        board[1][c] = ('P','b')
        board[6][c] = ('P','w')
    return board

# ── Move Generation ────────────────────────────────────────────────────────────
def in_bounds(r,c): return 0<=r<8 and 0<=c<8

def raw_moves(board, r, c, last_move, _castling=True):
    cell = board[r][c]
    if cell is None: return []
    piece, color = cell
    opp = 'b' if color=='w' else 'w'
    moves = []

    def slide(dr,dc):
        nr,nc = r+dr,c+dc
        while in_bounds(nr,nc):
            if board[nr][nc] is None: moves.append((nr,nc))
            elif board[nr][nc][1]==opp: moves.append((nr,nc)); break
            else: break
            nr+=dr; nc+=dc

    if piece=='P':
        fwd = -1 if color=='w' else 1
        sr  =  6 if color=='w' else 1
        if in_bounds(r+fwd,c) and board[r+fwd][c] is None:
            moves.append((r+fwd,c))
            if r==sr and board[r+2*fwd][c] is None:
                moves.append((r+2*fwd,c))
        for dc in (-1,1):
            nr,nc = r+fwd,c+dc
            if in_bounds(nr,nc):
                if board[nr][nc] and board[nr][nc][1]==opp:
                    moves.append((nr,nc))
                if last_move:
                    (lr0,lc0),(lr1,lc1),lp = last_move
                    if lp=='P' and lc1==nc and lr1==r and abs(lr0-lr1)==2:
                        moves.append((nr,nc))
    elif piece=='N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr,nc = r+dr,c+dc
            if in_bounds(nr,nc) and (board[nr][nc] is None or board[nr][nc][1]==opp):
                moves.append((nr,nc))
    elif piece=='B':
        for d in [(-1,-1),(-1,1),(1,-1),(1,1)]: slide(*d)
    elif piece=='R':
        for d in [(-1,0),(1,0),(0,-1),(0,1)]: slide(*d)
    elif piece=='Q':
        for d in [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]: slide(*d)
    elif piece=='K':
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==dc==0: continue
                nr,nc = r+dr,c+dc
                if in_bounds(nr,nc) and (board[nr][nc] is None or board[nr][nc][1]==opp):
                    moves.append((nr,nc))
        if _castling and not has_moved(board,r,c) and not in_check(board,color):
            if (board[r][7]==('R',color) and board[r][5] is None and board[r][6] is None and
                    not sq_attacked(board,r,5,opp) and not sq_attacked(board,r,6,opp)):
                moves.append((r,6))
            if (board[r][0]==('R',color) and board[r][1] is None and board[r][2] is None and
                    board[r][3] is None and not sq_attacked(board,r,3,opp) and
                    not sq_attacked(board,r,2,opp)):
                moves.append((r,2))
    return moves

def has_moved(board,r,c):
    cell=board[r][c]
    if cell is None: return True
    p,col=cell
    return p=='K' and (r,c)!=((7,4) if col=='w' else (0,4))

def sq_attacked(board,r,c,by):
    for rr in range(8):
        for cc in range(8):
            if board[rr][cc] and board[rr][cc][1]==by:
                if (r,c) in raw_moves(board,rr,cc,None,_castling=False):
                    return True
    return False

def find_king(board,color):
    for r in range(8):
        for c in range(8):
            if board[r][c]==('K',color): return r,c
    return None

def in_check(board,color):
    k=find_king(board,color)
    if k is None: return False
    return sq_attacked(board,k[0],k[1],'b' if color=='w' else 'w')

def apply_move(board,r,c,nr,nc):
    b=copy.deepcopy(board)
    piece,color=b[r][c]
    b[nr][nc]=b[r][c]; b[r][c]=None
    if piece=='P' and c!=nc and b[nr][nc] is None: b[r][nc]=None
    if piece=='K':
        if nc==c+2: b[nr][7]=None; b[nr][5]=('R',color)
        if nc==c-2: b[nr][0]=None; b[nr][3]=('R',color)
    if piece=='P' and (nr==0 or nr==7): b[nr][nc]=('Q',color)
    return b

def legal_moves(board,r,c,last_move):
    pc=board[r][c][1]
    return [(nr,nc) for nr,nc in raw_moves(board,r,c,last_move)
            if not in_check(apply_move(board,r,c,nr,nc),pc)]

def all_legal_moves(board,color,last_move):
    out=[]
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][1]==color:
                for dst in legal_moves(board,r,c,last_move):
                    out.append(((r,c),dst))
    return out

# ── Move notation: Pe2 -> Pe3 format ──────────────────────────────────────────
def sq_name(r,c):
    """Convert board coords to square name like e2."""
    return FILES[c] + str(8-r)

def move_notation(piece, src, dst, is_castle_k, is_castle_q, promotion):
    """Return string like Pe2->Pe3, or O-O / O-O-O for castling."""
    if is_castle_k: return 'O-O'
    if is_castle_q: return 'O-O-O'
    p = 'Q' if promotion else piece   # promoted pawn becomes Q
    return f"{p}{sq_name(*src)} -> {p}{sq_name(*dst)}"

# ── AI ─────────────────────────────────────────────────────────────────────────
PIECE_VALUES = {'P':100,'N':320,'B':330,'R':500,'Q':900,'K':20000}
PST = {
    'P':[ 0, 0, 0, 0, 0, 0, 0, 0, 50,50,50,50,50,50,50,50,
          10,10,20,30,30,20,10,10,  5, 5,10,25,25,10, 5, 5,
           0, 0, 0,20,20, 0, 0, 0,  5,-5,-10,0, 0,-10,-5,5,
           5,10,10,-20,-20,10,10,5, 0, 0, 0, 0, 0, 0, 0, 0],
    'N':[-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,0,0,0,-20,-40,
         -30,0,10,15,15,10,0,-30,-30,5,15,20,20,15,5,-30,
         -30,0,15,20,20,15,0,-30,-30,5,10,15,15,10,5,-30,
         -40,-20,0,5,5,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50],
    'B':[-20,-10,-10,-10,-10,-10,-10,-20,-10,0,0,0,0,0,0,-10,
         -10,0,5,10,10,5,0,-10,-10,5,5,10,10,5,5,-10,
         -10,0,10,10,10,10,0,-10,-10,10,10,10,10,10,10,-10,
         -10,5,0,0,0,0,5,-10,-20,-10,-10,-10,-10,-10,-10,-20],
    'R':[ 0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5,
         -5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,
         -5,0,0,0,0,0,0,-5,-5,0,0,0,0,0,0,-5,
         -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0],
    'Q':[-20,-10,-10,-5,-5,-10,-10,-20,-10,0,0,0,0,0,0,-10,
         -10,0,5,5,5,5,0,-10,-5,0,5,5,5,5,0,-5,
          0,0,5,5,5,5,0,-5,-10,5,5,5,5,5,0,-10,
         -10,0,5,0,0,0,0,-10,-20,-10,-10,-5,-5,-10,-10,-20],
    'K':[-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,
         -30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,
         -20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10,
          20,20,0,0,0,0,20,20,20,30,10,0,0,10,30,20],
}

def evaluate(board):
    s=0
    for r in range(8):
        for c in range(8):
            cell=board[r][c]
            if not cell: continue
            p,col=cell
            idx=r*8+c if col=='w' else (7-r)*8+c
            v=PIECE_VALUES[p]+PST[p][idx]
            s+=v if col=='w' else -v
    return s

def minimax(board,depth,alpha,beta,maxing,last_move):
    color='w' if maxing else 'b'
    moves=all_legal_moves(board,color,last_move)
    if not moves: return (10000 if not maxing else -10000),None
    if depth==0: return evaluate(board),None
    best_move=None
    if maxing:
        best=-999999
        for src,dst in moves:
            b2=apply_move(board,src[0],src[1],dst[0],dst[1])
            pc=board[src[0]][src[1]][0]
            sc2,_=minimax(b2,depth-1,alpha,beta,False,(src,dst,pc))
            if sc2>best: best=sc2; best_move=(src,dst)
            alpha=max(alpha,best)
            if beta<=alpha: break
    else:
        best=999999
        for src,dst in moves:
            b2=apply_move(board,src[0],src[1],dst[0],dst[1])
            pc=board[src[0]][src[1]][0]
            sc2,_=minimax(b2,depth-1,alpha,beta,True,(src,dst,pc))
            if sc2<best: best=sc2; best_move=(src,dst)
            beta=min(beta,best)
            if beta<=alpha: break
    return best,best_move

AI_DEPTH=3

def cpu_think(board,last_move,result):
    _,move=minimax(board,AI_DEPTH,-999999,999999,False,last_move)
    result[0]=move

# ── Coord helpers ──────────────────────────────────────────────────────────────
def b2s(r,c): return BOARD_X+c*CELL, BOARD_Y+r*CELL

def s2b(x,y):
    c=(x-BOARD_X)//CELL; r=(y-BOARD_Y)//CELL
    return (r,c) if 0<=r<8 and 0<=c<8 else None

# ── Drawing: Board ─────────────────────────────────────────────────────────────
def draw_board(surf, selected, highlights, check_sq, move_dots, cpu_hl):
    hl=pygame.Surface((CELL,CELL),pygame.SRCALPHA)
    for r in range(8):
        for c in range(8):
            x,y=b2s(r,c)
            pygame.draw.rect(surf, LIGHT if (r+c)%2==0 else DARK,(x,y,CELL,CELL))
    for r,c in cpu_hl:
        x,y=b2s(r,c); hl.fill(CPU_MOVE); surf.blit(hl,(x,y))
    for r,c in highlights:
        x,y=b2s(r,c); hl.fill(HIGHLIGHT); surf.blit(hl,(x,y))
    if selected:
        x,y=b2s(*selected); hl.fill(SELECTED); surf.blit(hl,(x,y))
    if check_sq:
        x,y=b2s(*check_sq); hl.fill(CHECK_CLR); surf.blit(hl,(x,y))
    for r,c in move_dots:
        x,y=b2s(r,c)
        ds=pygame.Surface((CELL,CELL),pygame.SRCALPHA); ds.fill((0,0,0,0))
        pygame.draw.circle(ds,MOVE_DOT,(CELL//2,CELL//2),CELL//6)
        surf.blit(ds,(x,y))

def draw_labels(surf,font):
    for i in range(8):
        surf.blit(font.render(FILES[i],True,(160,120,75)),
                  (BOARD_X+i*CELL+CELL//2-6, BOARD_Y+BOARD_SIZE+4))
        surf.blit(font.render(str(8-i),True,(160,120,75)),
                  (BOARD_X-18, BOARD_Y+i*CELL+CELL//2-9))

def draw_pieces(surf,board,pfont,dragging=None,drag_pos=None):
    for r in range(8):
        for c in range(8):
            if dragging and (r,c)==dragging: continue
            cell=board[r][c]
            if cell:
                p,col=cell; ch=UNICODE_PIECES[(p,col)]
                x,y=b2s(r,c)
                surf.blit(pfont.render(ch,True,(0,0,0)),(x+3,y+3))
                surf.blit(pfont.render(ch,True,(255,255,255) if col=='w' else (22,14,8)),(x+2,y))
    if dragging and drag_pos:
        cell=board[dragging[0]][dragging[1]]
        if cell:
            p,col=cell; ch=UNICODE_PIECES[(p,col)]
            rx,ry=drag_pos
            surf.blit(pfont.render(ch,True,(255,255,255) if col=='w' else (22,14,8)),(rx-CELL//2+2,ry-CELL//2))

def draw_status(surf,font,turn,status,thinking):
    if   status=='checkmate': msg=("Checkmate! CPU wins 🤖" if turn=='w' else "Checkmate! You win! 🎉")+"  —  R to restart"
    elif status=='stalemate': msg="Stalemate — Draw!  —  R to restart"
    elif thinking:            msg="CPU is thinking…"
    elif status=='check':     msg="Check!  —  Your move" if turn=='w' else "Check!  —  CPU's move"
    else:                     msg="Your move  (White)" if turn=='w' else "CPU's move  (Black)"
    txt=font.render(msg,True,W_TXT)
    # centered in status bar
    surf.blit(txt,((BOARD_X+BOARD_SIZE//2)-txt.get_width()//2, (STATUS_H-txt.get_height())//2))

# ── Drawing: Sidebar ───────────────────────────────────────────────────────────
def draw_sidebar(surf, fonts, score_w, score_b, cap_w, cap_b, move_log, scroll):
    hdr_f, mono_f, big_f, small_f, cap_f = fonts
    sx,sy,sw,sh = SIDE_X, SIDE_Y, SIDEBAR_W, SIDE_H

    # Panel
    pygame.draw.rect(surf,PANEL_BG,(sx,sy,sw,sh),border_radius=10)
    pygame.draw.rect(surf,PANEL_LINE,(sx,sy,sw,sh),1,border_radius=10)

    y = sy + 14

    # ── SCORE ─────────────────────────────────────────────────────────────────
    hd = hdr_f.render("SCORE", True, GOLD)
    surf.blit(hd,(sx+sw//2-hd.get_width()//2, y)); y += hd.get_height()+8

    bx   = sx+14; bar_w=sw-28; bar_h=32
    tot  = max(1, score_w+score_b)
    wf   = score_w/tot

    # background track
    pygame.draw.rect(surf,(40,32,24),(bx,y,bar_w,bar_h),border_radius=8)

    # white portion (left)
    if score_w>0:
        ww=max(1,int(bar_w*wf))
        pygame.draw.rect(surf,(225,215,195),(bx,y,ww,bar_h),
                         border_radius=8 if score_b==0 else 0)
        # round left corners always
        pygame.draw.rect(surf,(225,215,195),(bx,y,min(8,ww),bar_h))
        pygame.draw.rect(surf,(225,215,195),(bx,y,ww,bar_h),border_radius=8 if score_b==0 else 0)

    # black portion (right)
    if score_b>0:
        bw2=bar_w-int(bar_w*wf)
        bx2=bx+int(bar_w*wf)
        pygame.draw.rect(surf,(55,44,33),(bx2,y,bw2,bar_h),
                         border_radius=8 if score_w==0 else 0)

    pygame.draw.rect(surf,PANEL_LINE,(bx,y,bar_w,bar_h),1,border_radius=8)

    # Score numbers — White score in near-black font, CPU score in near-white font
    ws_txt = big_f.render(str(score_w),True,B_TXT)   # dark text on light bar
    bs_txt = big_f.render(str(score_b),True,CPU_TXT)  # light text on dark bar
    surf.blit(ws_txt,(bx+6,          y+bar_h//2-ws_txt.get_height()//2))
    surf.blit(bs_txt,(bx+bar_w-bs_txt.get_width()-6, y+bar_h//2-bs_txt.get_height()//2))
    y += bar_h+4

    # Labels
    wl=small_f.render("You (White)",True,(170,160,145))
    bl=small_f.render("CPU (Black)",True,(100, 88, 70))
    surf.blit(wl,(bx,y)); surf.blit(bl,(bx+bar_w-bl.get_width(),y))
    y += wl.get_height()+12

    # ── CAPTURES ──────────────────────────────────────────────────────────────
    pygame.draw.line(surf,PANEL_LINE,(sx+10,y),(sx+sw-10,y)); y+=8

    chd=hdr_f.render("CAPTURES", True, GOLD)
    surf.blit(chd,(sx+sw//2-chd.get_width()//2,y)); y+=chd.get_height()+6

    def render_capture_row(pieces, show_as_color, label_txt, ypos):
        """Render captured pieces in descending order of value."""
        # sort by CAP_ORDER
        sorted_pieces = sorted(pieces, key=lambda p: CAP_ORDER.index(p) if p in CAP_ORDER else 99)
        lbl = small_f.render(label_txt, True, DIM)
        surf.blit(lbl,(sx+10,ypos)); ypos += lbl.get_height()+2
        xc = sx+10
        for p in sorted_pieces:
            ch  = UNICODE_PIECES[(p, show_as_color)]
            clr = (240,230,215) if show_as_color=='w' else (38,28,18)
            img = cap_f.render(ch, True, clr)
            if xc + img.get_width() > sx+sw-10:
                xc = sx+10; ypos += img.get_height()+1
            surf.blit(img,(xc,ypos))
            xc += img.get_width()+2
        return ypos + cap_f.get_height() + 6

    # White captured black pieces — show as black pieces
    y = render_capture_row(cap_w, 'b', "White captured:", y)
    # Black captured white pieces — show as white pieces
    y = render_capture_row(cap_b, 'w', "CPU captured:", y)

    y += 4

    # ── MOVE LOG ──────────────────────────────────────────────────────────────
    pygame.draw.line(surf,PANEL_LINE,(sx+10,y),(sx+sw-10,y)); y+=8

    mhd=hdr_f.render("MOVE LOG", True, GOLD)
    surf.blit(mhd,(sx+sw//2-mhd.get_width()//2,y)); y+=mhd.get_height()+6

    log_top  = y
    log_h    = sy+sh - y - 10
    log_rect = pygame.Rect(sx+6, log_top, sw-12, log_h)

    row_h       = mono_f.get_height()+4
    total_rows  = len(move_log)
    vis_rows    = max(1, log_h // row_h)
    max_scroll  = max(0, total_rows - vis_rows)
    scroll      = max(0, min(scroll, max_scroll))

    old_clip=surf.get_clip(); surf.set_clip(log_rect)

    for i in range(total_rows):
        ry = log_top + (i - scroll)*row_h
        if ry+row_h < log_top or ry > log_top+log_h: continue

        entry   = move_log[i]
        is_last = (i == total_rows-1)
        by_w    = entry['color']=='w'

        # row shade
        if i%2==0:
            pygame.draw.rect(surf,(36,28,20),(sx+6,ry,sw-12,row_h))

        # move number label  "1."  "2." etc
        num_txt = mono_f.render(f"{entry['num']}.", True, DIM)
        surf.blit(num_txt,(sx+10, ry+1))

        # player tag
        who     = "You" if by_w else "CPU"
        who_clr = (200,190,170) if by_w else (120,150,200)
        wt      = mono_f.render(f"[{who}]", True, who_clr)
        surf.blit(wt,(sx+10+num_txt.get_width()+4, ry+1))

        # the move itself
        move_clr = GOLD if (is_last and by_w) else ((140,200,255) if (is_last and not by_w) else W_TXT)
        mt = mono_f.render(entry['text'], True, move_clr)
        surf.blit(mt,(sx+10+num_txt.get_width()+wt.get_width()+8, ry+1))

    surf.set_clip(old_clip)

    if total_rows > vis_rows:
        hint=small_f.render("scroll ↑↓",True,(75,60,45))
        surf.blit(hint,(sx+sw-hint.get_width()-8, sy+sh-hint.get_height()-4))

    return scroll

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.FULLSCREEN)
    pygame.display.set_caption("Chess vs CPU")
    clock  = pygame.time.Clock()

    pfont   = pygame.font.SysFont("segoeuisymbol,symbola,freesans,dejavusans", CELL-4)
    lbl_f   = pygame.font.SysFont("georgia,serif", max(12,CELL//5))
    stat_f  = pygame.font.SysFont("georgia,serif", max(16,CELL//4), bold=True)
    hdr_f   = pygame.font.SysFont("georgia,serif", max(13,CELL//4), bold=True)
    mono_f  = pygame.font.SysFont("couriernew,dejavusansmono,monospace", max(12,CELL//5))
    big_f   = pygame.font.SysFont("georgia,serif", max(16,CELL//4), bold=True)
    small_f = pygame.font.SysFont("georgia,serif", max(11,CELL//6))
    cap_f   = pygame.font.SysFont("segoeuisymbol,symbola,freesans,dejavusans", max(16,CELL//4))
    sidebar_fonts = (hdr_f, mono_f, big_f, small_f, cap_f)

    move_counter = [0]  # mutable counter shared in closures

    def new_game():
        move_counter[0] = 0
        return dict(
            board        = init_board(),
            turn         = 'w',
            selected     = None,
            highlights   = [],
            cpu_hl       = [],
            move_dots    = [],
            last_move    = None,
            status       = 'normal',
            drag         = None,
            drag_pos     = None,
            check_sq     = None,
            cpu_thinking = False,
            cpu_result   = [None],
            cpu_thread   = None,
            score_w      = 0,
            score_b      = 0,
            cap_w        = [],   # black pieces captured by white (shown as black)
            cap_b        = [],   # white pieces captured by black (shown as white)
            move_log     = [],   # list of dicts {num, color, text}
            scroll       = 0,
        )

    state = new_game()

    def update_status(st):
        color=st['turn']
        moves=all_legal_moves(st['board'],color,st['last_move'])
        if not moves:
            st['status']  ='checkmate' if in_check(st['board'],color) else 'stalemate'
            st['check_sq']=find_king(st['board'],color) if st['status']=='checkmate' else None
        elif in_check(st['board'],color):
            st['status']  ='check'
            st['check_sq']=find_king(st['board'],color)
        else:
            st['status']  ='normal'
            st['check_sq']=None

    update_status(state)

    def commit_move(st, src, dst):
        board_before  = st['board']
        piece         = board_before[src[0]][src[1]][0]
        mover_color   = board_before[src[0]][src[1]][1]
        captured_cell = board_before[dst[0]][dst[1]]

        # en-passant
        ep_cap=None
        if piece=='P' and src[1]!=dst[1] and captured_cell is None:
            ep_cap=board_before[src[0]][dst[1]]
        actual_cap = captured_cell or ep_cap

        is_castle_k = piece=='K' and dst[1]-src[1]==2
        is_castle_q = piece=='K' and src[1]-dst[1]==2
        promotion   = piece=='P' and (dst[0]==0 or dst[0]==7)

        st['last_move']=(src,dst,piece)
        st['board']    =apply_move(board_before,src[0],src[1],dst[0],dst[1])
        st['turn']     ='b' if st['turn']=='w' else 'w'
        st['selected'] =None; st['move_dots']=[]
        st['highlights']=[src,dst]
        update_status(st)

        # captures & score
        if actual_cap:
            cp=actual_cap[0]
            pts=PIECE_SCORE.get(cp,0)
            if mover_color=='w': st['score_w']+=pts; st['cap_w'].append(cp)
            else:                st['score_b']+=pts; st['cap_b'].append(cp)

        # move log entry
        move_counter[0]+=1
        notation=move_notation(piece,src,dst,is_castle_k,is_castle_q,promotion)
        st['move_log'].append({'num':move_counter[0],'color':mover_color,'text':notation})

        # auto-scroll to bottom
        st['scroll']=len(st['move_log'])

    def start_cpu(st):
        st['cpu_thinking']=True; st['cpu_result']=[None]
        t=threading.Thread(target=cpu_think,
                           args=(st['board'],st['last_move'],st['cpu_result']),daemon=True)
        t.start(); st['cpu_thread']=t

    def select(st,r,c):
        board=st['board']
        if board[r][c] and board[r][c][1]==HUMAN_COLOR:
            st['selected']=(r,c)
            st['move_dots']=legal_moves(board,r,c,st['last_move'])
        else:
            st['selected']=None; st['move_dots']=[]

    def try_human_move(st,r,c):
        sel=st['selected']
        if sel is None: return
        if (r,c) in legal_moves(st['board'],sel[0],sel[1],st['last_move']):
            commit_move(st,sel,(r,c))
            st['cpu_hl']=[]
            if st['turn']==CPU_COLOR and st['status'] not in ('checkmate','stalemate'):
                start_cpu(st)
        else:
            select(st,r,c)

    running=True
    while running:
        clock.tick(FPS)
        mx,my=pygame.mouse.get_pos()
        if state['drag']: state['drag_pos']=(mx,my)

        if state['cpu_thinking'] and state['cpu_result'][0] is not None:
            state['cpu_thinking']=False
            src,dst=state['cpu_result'][0]
            commit_move(state,src,dst)
            state['cpu_hl']=[src,dst]

        for event in pygame.event.get():
            if event.type==pygame.QUIT: running=False
            elif event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,): running=False
                elif event.key==pygame.K_r: state=new_game(); update_status(state)
                elif event.key==pygame.K_UP:   state['scroll']=max(0,state['scroll']-1)
                elif event.key==pygame.K_DOWN: state['scroll']+=1
            elif event.type==pygame.MOUSEWHEEL:
                state['scroll']=max(0,state['scroll']-event.y)
            elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                if (state['turn']==HUMAN_COLOR and not state['cpu_thinking']
                        and state['status'] not in ('checkmate','stalemate')):
                    sq=s2b(mx,my)
                    if sq:
                        r,c=sq
                        if state['selected']:
                            if (r,c) in legal_moves(state['board'],state['selected'][0],
                                                    state['selected'][1],state['last_move']):
                                try_human_move(state,r,c)
                            else:
                                select(state,r,c)
                                if state['board'][r][c] and state['board'][r][c][1]==HUMAN_COLOR:
                                    state['drag']=(r,c)
                        else:
                            select(state,r,c)
                            if state['board'][r][c] and state['board'][r][c][1]==HUMAN_COLOR:
                                state['drag']=(r,c)
            elif event.type==pygame.MOUSEBUTTONUP and event.button==1:
                if state['drag']:
                    sq=s2b(mx,my)
                    if sq and state['status'] not in ('checkmate','stalemate'):
                        try_human_move(state,sq[0],sq[1])
                    state['drag']=None; state['drag_pos']=None

        # ── Draw ────────────────────────────────────────────────────────────────
        screen.fill(BG)

        # Status bar background
        pygame.draw.rect(screen,(28,22,16),(0,0,WIN_W,STATUS_H))
        pygame.draw.line(screen,PANEL_LINE,(0,STATUS_H),(WIN_W,STATUS_H))

        # Board border
        pygame.draw.rect(screen,BORDER,
                         (BOARD_X-5,BOARD_Y-5,BOARD_SIZE+10,BOARD_SIZE+10),5,border_radius=4)

        draw_board(screen,state['selected'],state['highlights'],
                   state['check_sq'],state['move_dots'],state['cpu_hl'])
        draw_labels(screen,lbl_f)
        draw_pieces(screen,state['board'],pfont,
                    dragging=state['drag'],drag_pos=state['drag_pos'])
        draw_status(screen,stat_f,state['turn'],state['status'],state['cpu_thinking'])

        if state['cpu_thinking']:
            dots='.'*(pygame.time.get_ticks()//400%4)
            screen.blit(stat_f.render(dots,True,(160,140,100)),
                        (BOARD_X+BOARD_SIZE//2+140,(STATUS_H-stat_f.get_height())//2))

        # ESC hint bottom-left
        esc=lbl_f.render("ESC=quit  R=restart",True,(70,55,40))
        screen.blit(esc,(BOARD_X, WIN_H-esc.get_height()-6))

        state['scroll']=draw_sidebar(
            screen, sidebar_fonts,
            state['score_w'],state['score_b'],
            state['cap_w'],  state['cap_b'],
            state['move_log'],state['scroll']
        )

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__=='__main__':
    main()