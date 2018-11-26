from PyQt5.QtWidgets import QWidget, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
import requests
from chessboard import chessboard as CB

D_PIECE = 36
R_PIECE = D_PIECE / 2
WIDTH_CHESSBOARD = 715
HEIGHT_CHESSBOARD = 689
MARGIN = 20
GRID_W = (WIDTH_CHESSBOARD - (MARGIN * 2)) / 14
GRID_H = (HEIGHT_CHESSBOARD - (MARGIN* 2)) / 14


# main gaming UI
class Gomoku(QWidget):

    end_game_signal = pyqtSignal(int)

    def __init__(self, 
                isMaster, 
                roomName,  
                masterName, 
                guestName, 
                masterStone, 
                serverIp, 
                websocket, 
                backHook,
                watch_game=False):
        super().__init__()

        self.end_game_signal.connect(self.showGameEnd)

        self.watch_game = watch_game

        self.step_no = 0
        self.oth_step = 0
        self.isMaster = isMaster

        if self.isMaster:
            self.userName = masterName
        else:
            self.userName = guestName

        self.roomName = roomName

        # if self.watch_game:
        #     uri = 'ws://' + serverIp + ':8080/playing'
            
        #     headers = [("role", 'a'), 
        #         ("roomName", roomName),
        #         ("userName", websocket),
        #         ("masterStone", 1)]
        # else:
        self.ws = websocket

        self.backHook = backHook
        self.serverIp = serverIp

        if masterStone == 1:
            self.username_b = masterName
            self.username_w = guestName
            self.putStone = self.isMaster
        else:
            self.username_w = masterName
            self.username_b = guestName
            self.putStone = not self.isMaster

        if self.putStone:
            self.my_stone = 1
        else:
            self.my_stone = 2
        
        #self.ws = socketCli(uri, headers=headers)
        
        self.resetSocketHook()

        self.restart()

    def restart(self):    
        #CB init
        # self.obj = CB()
        # self.obj.reset()
        self.winnervalue = 0
        self.showchessboard()

        self.gamestart()
        self.setMouseTracking(True)
    
    def showchessboard(self):
        # init user interface
        self.setGeometry(330, 70, WIDTH_CHESSBOARD + 200, HEIGHT_CHESSBOARD) # set window size
        self.setWindowTitle("Gomoku Game") # set window title
        self.setWindowIcon(QIcon('chessboard/gomoku_icon.png')) # set window icon
        self.chessboard14 = QPixmap('chessboard/chessboard14.png') # set background
        self.black = QPixmap('chessboard/black.png') # set black piece
        self.white = QPixmap('chessboard/white.png') # set white piece
        self.manyblack = QPixmap('chessboard/manyblack.png') # set many black
        self.manywhite = QPixmap('chessboard/manywhite.png') # set many white
        self.setCursor(Qt.PointingHandCursor) # set mouse shape
        # show chessboard
        background = QLabel(self)
        background.setPixmap(self.chessboard14)
        background.setScaledContents(True)
        # show many black
        user_black = QLabel(self)
        user_black.setPixmap(self.manyblack)
        user_black.move(720, 10)
        # show many white
        user_white = QLabel(self)
        user_white.setPixmap(self.manywhite)
        user_white.move(720, HEIGHT_CHESSBOARD - 195)
        # show playername in black
        player_black = QLabel(self)
        player_black.setText("Black:    " + self.username_b)
        player_black.move(750, 220)
        player_black.setFont(QFont("Roman times", 16, QFont.Bold))
        # show playername in white
        player_white = QLabel(self)
        player_white.setText("White:    " + self.username_w)
        player_white.move(750, HEIGHT_CHESSBOARD - 230)
        player_white.setFont(QFont("Roman times", 16, QFont.Bold))
        
    def gamestart(self):
        #game start
        #location of a piece
        self.piece = QLabel(self)
        self.piece.setMouseTracking(True)
        self.piece.pos = None
        # draw a piece, total 15 *15
        self.put = [QLabel(self) for i in range(15 * 15)]
        # self.step = 1
        if self.putStone:
            self.color = self.black
        else:
            self.color = self.white
        
        if self.watch_game:
            self.ws.connect()
        # self.colornum = 1
    
    def mouseReleaseEvent(self, event):
        if self.putStone:
            #self.putStone = False

            self.piece.pos = event.pos()
            if self.piece.pos:
                self.i = round((self.piece.pos.x() - MARGIN) / GRID_W)
                self.j = round((self.piece.pos.y() - MARGIN) / GRID_H)

            toSend = self.encode(self.i, self.j)

            self.ws.send(toSend)

    def encode(self, x, y):
        message = x
        message |= (y << 4)
        message |= (self.my_stone << 8)
        message |= (self.step_no << 10)
        return str(message)

    def paint(self, event):
        if self.piece.pos:
            self.put[self.step].setPixmap(self.color)
            if self.i != None and self.j != None:
                x = MARGIN + self.i * GRID_W - R_PIECE
                y = MARGIN + self.j * GRID_H - R_PIECE
                self.put[self.step].setGeometry(x, y, D_PIECE, D_PIECE) # draw piece to grid

    def paint(self, i, j, color):
        self.put[self.step_no + self.oth_step].setPixmap(color)
        x = MARGIN + i * GRID_W - R_PIECE
        y = MARGIN + j * GRID_H - R_PIECE
        self.put[self.step_no + self.oth_step].setGeometry(x, y, D_PIECE, D_PIECE) # draw piece to grid

        if self.watch_game:
            self.step_no += 1

    def put_a_stone(self, pos_by_int):
        x = pos_by_int & 0b1111
        y = (pos_by_int >> 4) & 0b1111
        player = (pos_by_int >> 8) & 0b11
        step = (pos_by_int >> 10) & 0b1111_1111
        win_flag = (pos_by_int >> 18) & 0b111

        print('step: %d, x: %d ,y: %d, p: %d, win_flag: %d' % (step, x, y, player, win_flag))

        if player == 1:
            self.paint(x, y, self.black)
        else:
            self.paint(x, y, self.white)
        if not self.watch_game:
            if self.my_stone == player:
                self.step_no = step + 1
                self.putStone = False
            else:
                self.oth_step = step + 1
                self.putStone = True
        if win_flag == 0:
            pass
        elif win_flag == 1:
            print("black win")
            self.end_game_signal.emit(1)
        elif win_flag == 2:
            print("white win")
            self.end_game_signal.emit(2)
        elif win_flag == 3:
            print("LOL")
            self.end_game_signal.emit(3)

        self.update()
    
    @pyqtSlot(int)
    def showGameEnd(self, winner):
        if self.watch_game:
            if winner == 3:
                info = "Draw. lol"
            elif winner == 1:
                info = "Black win!"
            elif winner == 2:
                info = "White win!"
            elif winner == 6:
                info = "Someone quitted."
            button = QMessageBox.question(self,"Info",  
                                      info,  
                                      QMessageBox.Ok,  
                                      QMessageBox.Ok)
            if button == QMessageBox.Ok:
                self.backHook()
                self.close()
            else:
                self.close()
                raise SystemExit(0)
            return

        if winner == 3:
            info = "Draw. lol"
        else:
            if winner == 6:
                info = "Your opponent quitted."
            elif winner == self.my_stone:
                info = "You win! Nice!"
            else:
                info = "You lose."
        button = QMessageBox.question(self,"Info",  
                                      info,  
                                      QMessageBox.Ok,  
                                      QMessageBox.Ok)
        if button == QMessageBox.Ok:
            self.backHook()
            self.close()
        else:
            self.close()
            raise SystemExit(0)

    def resetSocketHook(self):
        self.ws.hook(self)

    def handleMessage(self, message):
        print("Received: ", message)
        if message[0] == 'J':
            # join signal
            print("Should not receive join signal: ", message)
        else:
            try:
                signal = int(message)
                if signal < 0:
                    # START_SIGNAL = -1
                    # GUEST_READY_SIGNAL = -2
                    # GUEST_UNREADY_SIGNAL = -3
                    # GUEST_LEAVE_SIGNAL = -4
                    # MASTER_DELETE_SIGNAL = -5
                    # END_SIGNAL = -6
                    
                    if signal == -6:
                        self.end_game_signal.emit(6)
                    else:
                        print("Should not receive other control signals: ", signal)
                else:
                    # moving signal
                    self.put_a_stone(signal)
            except:
                print("Unvalid message format.")