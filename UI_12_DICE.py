import tkinter as tk
import random
import time
from tkinter import font, messagebox
from collections import Counter
import threading

class KingdomComeDiceGame:
    def __init__(self, root):
        self.root = root
        self.root.title("对战盗圣亨利")
        
        # 设置窗口为16:9比例
        window_width = 1280
        window_height = 720
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.configure(bg="#2E4A33")  # 深绿色的桌面背景
        
        # 创建自定义字体
        self.button_font = font.Font(family="Arial", size=12, weight="bold")
        self.score_font = font.Font(family="Arial", size=14, weight="bold")
        self.dice_font = font.Font(family="Arial", size=24, weight="bold")
        self.rule_title_font = font.Font(family="Arial", size=16, weight="bold")
        self.rule_font = font.Font(family="Arial", size=12)
        
        # 游戏设置
        self.WINNING_SCORE = 4000  # 胜利所需分数
        
        # 设置玩家数据
        self.player_score = 0
        self.player_round_score = 0
        self.opponent_score = 0
        self.opponent_round_score = 0
        
        # 骰子状态
        self.player_dice = [1, 1, 1, 1, 1, 1]  # 初始值
        self.opponent_dice = [1, 1, 1, 1, 1, 1]  # 初始值
        self.player_selected_dice = []  # 本次掷出后玩家选中的骰子索引
        self.player_locked_dice = []    # 玩家已锁定的骰子索引
        self.opponent_locked_dice = []  # 亨利已锁定的骰子索引
        self.opponent_selected_dice = [] # 亨利当前选中的骰子索引
        
        # 当前选择的得分
        self.current_selection_score = 0
        self.pending_score = 0  # 待确认的分数
        
        # 游戏状态
        self.current_player = "player"  # 当前玩家，"player"或"opponent"
        self.dice_rolled = False        # 本回合是否已掷骰子
        self.awaiting_selection = False # 是否等待玩家选择得分骰子
        self.has_valid_selection = False # 是否有有效的选择
        self.game_in_progress = True    # 游戏是否正在进行
        self.opponent_is_playing = False # 亨利是否正在进行回合
        
        # AI亨利的风险参数
        self.ai_risk_factor = 0.7  # 0-1之间，越高表示越冒险
        
        # 创建互斥锁，防止用户在AI回合操作
        self.game_lock = threading.Lock()
        
        self.create_game_layout()
        self.update_buttons_state()
    
    def create_game_layout(self):
        # 创建主框架
        main_frame = tk.Frame(self.root, bg="#2E4A33")
        main_frame.pack(fill="both", expand=True)
        
        # 创建游戏区域（左侧）和规则区域（右侧）
        game_frame = tk.Frame(main_frame, bg="#2E4A33", width=900)
        rules_frame = tk.Frame(main_frame, bg="#3A5A43", width=380)
        
        game_frame.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        rules_frame.pack(side="right", fill="both", expand=False, padx=(0, 10), pady=10)
        
        # 设置game_frame内部元素
        # 创建中间分界线
        separator = tk.Frame(game_frame, height=4, bg="#D4AF37", relief="raised")
        separator.pack(fill="x", pady=10)
        
        # 创建亨利区域 (上半部分)
        opponent_frame = tk.Frame(game_frame, bg="#2E4A33")
        opponent_frame.pack(fill="both", expand=True, padx=20, pady=(20, 0))
        
        # 亨利信息和分数
        opponent_info_frame = tk.Frame(opponent_frame, bg="#2E4A33")
        opponent_info_frame.pack(side="top", fill="x", pady=10)
        
        tk.Label(opponent_info_frame, text="亨利", font=self.score_font, bg="#2E4A33", fg="white").pack(side="left")
        
        self.opponent_score_label = tk.Label(opponent_info_frame, text=f"总分: {self.opponent_score}", 
                                            font=self.score_font, bg="#2E4A33", fg="white")
        self.opponent_score_label.pack(side="right")
        
        self.opponent_round_label = tk.Label(opponent_info_frame, text=f"本轮得分: {self.opponent_round_score}", 
                                           font=self.score_font, bg="#2E4A33", fg="white")
        self.opponent_round_label.pack(side="right", padx=20)
        
        # 亨利骰子区域
        opponent_dice_frame = tk.Frame(opponent_frame, bg="#2E4A33")
        opponent_dice_frame.pack(fill="x", pady=10)
        
        self.opponent_dice_labels = []
        for i in range(6):
            dice_label = tk.Label(opponent_dice_frame, text=self.get_dice_face(self.opponent_dice[i]), 
                                 font=self.dice_font, bg="#4A7554", fg="white",
                                 width=2, height=1, relief="raised")
            dice_label.pack(side="left", padx=10)
            self.opponent_dice_labels.append(dice_label)
        
        # 创建玩家区域 (下半部分)
        player_frame = tk.Frame(game_frame, bg="#2E4A33")
        player_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # 当前选择得分显示区域
        selection_frame = tk.Frame(player_frame, bg="#2E4A33")
        selection_frame.pack(fill="x", pady=5)
        
        tk.Label(selection_frame, text="当前选择得分:", font=self.score_font, 
                bg="#2E4A33", fg="white").pack(side="left")
        
        self.selection_score_label = tk.Label(selection_frame, text="0", 
                                            font=self.score_font, bg="#2E4A33", fg="#FFD700")
        self.selection_score_label.pack(side="left", padx=10)
        
        # 玩家骰子区域
        player_dice_frame = tk.Frame(player_frame, bg="#2E4A33")
        player_dice_frame.pack(fill="x", pady=10)
        
        self.player_dice_buttons = []
        for i in range(6):
            dice_button = tk.Button(player_dice_frame, text=self.get_dice_face(self.player_dice[i]), 
                                   font=self.dice_font, bg="#4A7554", fg="white",
                                   relief="raised", width=2, height=1,
                                   command=lambda idx=i: self.toggle_dice_selection(idx))
            dice_button.pack(side="left", padx=10)
            self.player_dice_buttons.append(dice_button)
        
        # 玩家按钮区域
        button_frame = tk.Frame(player_frame, bg="#2E4A33")
        button_frame.pack(fill="x", pady=20)
        
        self.roll_button = tk.Button(button_frame, text="掷骰子", font=self.button_font, 
                                   bg="#D4AF37", fg="black", padx=20, pady=10, command=self.roll_dice)
        self.roll_button.pack(side="left", padx=20)
        
        self.end_turn_button = tk.Button(button_frame, text="回合结束", font=self.button_font, 
                                      bg="#D4AF37", fg="black", padx=20, pady=10, command=self.end_turn)
        self.end_turn_button.pack(side="left", padx=20)
        
        # 消息显示区域
        self.message_label = tk.Label(button_frame, text="", font=self.button_font, 
                                     bg="#2E4A33", fg="white", wraplength=300)
        self.message_label.pack(side="left", padx=20)
        
        # 玩家信息和分数
        player_info_frame = tk.Frame(player_frame, bg="#2E4A33")
        player_info_frame.pack(side="bottom", fill="x", pady=10)
        
        tk.Label(player_info_frame, text="玩家", font=self.score_font, bg="#2E4A33", fg="white").pack(side="left")
        
        self.player_score_label = tk.Label(player_info_frame, text=f"总分: {self.player_score}", 
                                         font=self.score_font, bg="#2E4A33", fg="white")
        self.player_score_label.pack(side="right")
        
        self.player_round_label = tk.Label(player_info_frame, text=f"本轮得分: {self.player_round_score}", 
                                         font=self.score_font, bg="#2E4A33", fg="white")
        self.player_round_label.pack(side="right", padx=20)
        
        # 创建规则区域内容 (右侧)
        # 垂直分隔线
        separator = tk.Frame(rules_frame, width=2, bg="#D4AF37")
        separator.pack(side="left", fill="y", padx=(0, 10))
        
        # 规则内容框架
        rules_content = tk.Frame(rules_frame, bg="#3A5A43")
        rules_content.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # 规则标题
        title_label = tk.Label(rules_content, text="计分规则", font=self.rule_title_font, 
                              bg="#3A5A43", fg="#FFD700")
        title_label.pack(pady=(10, 20))
        
        # 基本规则说明
        basic_rules_frame = tk.Frame(rules_content, bg="#3A5A43")
        basic_rules_frame.pack(fill="x", pady=5)
        
        tk.Label(basic_rules_frame, text="单个骰子得分:", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w")
        
        # 1和5的得分规则
        single_dice_frame = tk.Frame(rules_content, bg="#3A5A43")
        single_dice_frame.pack(fill="x", pady=5, padx=10)
        
        # 1点得分
        one_frame = tk.Frame(single_dice_frame, bg="#3A5A43")
        one_frame.pack(fill="x", pady=2)
        tk.Label(one_frame, text=self.get_dice_face(1), font=self.rule_font, 
                bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=(0, 5))
        tk.Label(one_frame, text="= 100分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left")
        
        # 5点得分
        five_frame = tk.Frame(single_dice_frame, bg="#3A5A43")
        five_frame.pack(fill="x", pady=2)
        tk.Label(five_frame, text=self.get_dice_face(5), font=self.rule_font, 
                bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=(0, 5))
        tk.Label(five_frame, text="= 50分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left")
        
        # 分隔
        tk.Frame(rules_content, height=1, bg="#D4AF37").pack(fill="x", pady=10)
        
        # 组合规则
        tk.Label(rules_content, text="三个相同骰子得分:", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w", pady=(5, 0))
        
        # 三连得分规则
        triples_frame = tk.Frame(rules_content, bg="#3A5A43")
        triples_frame.pack(fill="x", pady=5, padx=10)
        
        # 三个1
        triple_one_frame = tk.Frame(triples_frame, bg="#3A5A43")
        triple_one_frame.pack(fill="x", pady=2)
        for i in range(3):
            tk.Label(triple_one_frame, text=self.get_dice_face(1), font=self.rule_font, 
                    bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=1)
        tk.Label(triple_one_frame, text="= 1000分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left", padx=(5, 0))
        
        # 三个其他数字
        triple_other_frame = tk.Frame(triples_frame, bg="#3A5A43")
        triple_other_frame.pack(fill="x", pady=2)
        tk.Label(triple_other_frame, text="三个 2-6 = 点数 × 100", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w")
        
        # 分隔
        tk.Frame(rules_content, height=1, bg="#D4AF37").pack(fill="x", pady=10)
        
        # 额外骰子规则
        tk.Label(rules_content, text="四个或更多相同骰子:", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w", pady=(5, 0))
        
        extra_dice_frame = tk.Frame(rules_content, bg="#3A5A43")
        extra_dice_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(extra_dice_frame, text="每多一颗相同骰子，分数翻倍", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w")
        
        # 示例
        examples_frame = tk.Frame(rules_content, bg="#3A5A43")
        examples_frame.pack(fill="x", pady=5, padx=10)
        
        # 四个1的例子
        four_ones_frame = tk.Frame(examples_frame, bg="#3A5A43")
        four_ones_frame.pack(fill="x", pady=2)
        for i in range(4):
            tk.Label(four_ones_frame, text=self.get_dice_face(1), font=self.rule_font, 
                    bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=1)
        tk.Label(four_ones_frame, text="= 2000分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left", padx=(5, 0))
        
        # 四个5的例子
        four_fives_frame = tk.Frame(examples_frame, bg="#3A5A43")
        four_fives_frame.pack(fill="x", pady=2)
        for i in range(4):
            tk.Label(four_fives_frame, text=self.get_dice_face(5), font=self.rule_font, 
                    bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=1)
        tk.Label(four_fives_frame, text="= 1000分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left", padx=(5, 0))
        
        # 分隔
        tk.Frame(rules_content, height=1, bg="#D4AF37").pack(fill="x", pady=10)
        
        # 特殊组合
        tk.Label(rules_content, text="特殊组合:", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w", pady=(5, 0))
        
        special_frame = tk.Frame(rules_content, bg="#3A5A43")
        special_frame.pack(fill="x", pady=5, padx=10)
        
        # 顺子
        straight_frame = tk.Frame(special_frame, bg="#3A5A43")
        straight_frame.pack(fill="x", pady=2)
        for i in range(1, 7):
            tk.Label(straight_frame, text=self.get_dice_face(i), font=self.rule_font, 
                    bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=1)
        tk.Label(straight_frame, text="= 1500分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left", padx=(5, 0))
        
        # 12345组合
        small_straight1_frame = tk.Frame(special_frame, bg="#3A5A43")
        small_straight1_frame.pack(fill="x", pady=2)
        for i in range(1, 6):
            tk.Label(small_straight1_frame, text=self.get_dice_face(i), font=self.rule_font, 
                    bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=1)
        tk.Label(small_straight1_frame, text="= 500分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left", padx=(5, 0))
        
        # 23456组合
        small_straight2_frame = tk.Frame(special_frame, bg="#3A5A43")
        small_straight2_frame.pack(fill="x", pady=2)
        for i in range(2, 7):
            tk.Label(small_straight2_frame, text=self.get_dice_face(i), font=self.rule_font, 
                    bg="#4A7554", fg="white", width=2, relief="raised").pack(side="left", padx=1)
        tk.Label(small_straight2_frame, text="= 750分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(side="left", padx=(5, 0))
        
        # 三对
        three_pairs_frame = tk.Frame(special_frame, bg="#3A5A43")
        three_pairs_frame.pack(fill="x", pady=2)
        tk.Label(three_pairs_frame, text="三对 (如 1-1-2-2-3-3) = 1500分", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w")
        
        # 分隔
        tk.Frame(rules_content, height=1, bg="#D4AF37").pack(fill="x", pady=10)
        
        # 游戏规则
        game_rules_frame = tk.Frame(rules_content, bg="#3A5A43")
        game_rules_frame.pack(fill="x", pady=5)
        
        tk.Label(game_rules_frame, text="游戏规则:", font=self.rule_font, 
                bg="#3A5A43", fg="white").pack(anchor="w", pady=(5, 0))
        
        rules_list_frame = tk.Frame(game_rules_frame, bg="#3A5A43")
        rules_list_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(rules_list_frame, text="• 选择得分骰子后可继续掷或结束回合", 
                font=self.rule_font, bg="#3A5A43", fg="white",
                wraplength=330, justify="left").pack(anchor="w", pady=2)
        
        tk.Label(rules_list_frame, text="• 如果掷骰无可得分组合，本回合分数清零", 
                font=self.rule_font, bg="#3A5A43", fg="white",
                wraplength=330, justify="left").pack(anchor="w", pady=2)
        
        tk.Label(rules_list_frame, text="• 所有骰子都得分后，可重新掷全部骰子", 
                font=self.rule_font, bg="#3A5A43", fg="white",
                wraplength=330, justify="left").pack(anchor="w", pady=2)
        
        tk.Label(rules_list_frame, text="• 率先达到4000分获胜", 
                font=self.rule_font, bg="#3A5A43", fg="white",
                wraplength=330, justify="left").pack(anchor="w", pady=2)
    
    def get_dice_face(self, value):
        """返回骰子面的Unicode字符"""
        dice_faces = {
            1: "⚀", 
            2: "⚁", 
            3: "⚂", 
            4: "⚃", 
            5: "⚄", 
            6: "⚅"
        }
        return dice_faces.get(value, "?")
    
    def update_dice_display(self):
        """更新骰子显示"""
        if not self.game_in_progress:
            return
            
        # 更新玩家骰子
        for i, button in enumerate(self.player_dice_buttons):
            button.config(text=self.get_dice_face(self.player_dice[i]))
            
            # 设置骰子按钮的状态和颜色
            if i in self.player_locked_dice:
                button.config(bg="#696969", fg="white", state="disabled")  # 锁定的骰子显示为灰色
            elif i in self.player_selected_dice:
                button.config(bg="#FFD700", fg="black")  # 选中的骰子显示为金色，黑色文字
            else:
                if self.awaiting_selection and self.current_player == "player" and not self.opponent_is_playing:
                    button.config(bg="#4A7554", fg="white", state="normal")  # 可选状态为绿色
                else:
                    button.config(bg="#4A7554", fg="white", state="disabled")  # 不可选状态
        
        # 更新亨利骰子
        for i, label in enumerate(self.opponent_dice_labels):
            label.config(text=self.get_dice_face(self.opponent_dice[i]))
            
            # 设置亨利骰子的颜色
            if i in self.opponent_locked_dice:
                label.config(bg="#696969", fg="white")  # 锁定的骰子显示为灰色
            elif i in self.opponent_selected_dice:
                label.config(bg="#FFD700", fg="black")  # 选中的骰子显示为金色
            else:
                label.config(bg="#4A7554", fg="white")  # 正常背景
        
        # 立即更新UI
        self.root.update()
    
    def update_score_display(self):
        """更新分数显示"""
        if not self.game_in_progress:
            return
            
        self.player_score_label.config(text=f"总分: {self.player_score}")
        self.player_round_label.config(text=f"本轮得分: {self.player_round_score}")
        self.opponent_score_label.config(text=f"总分: {self.opponent_score}")
        self.opponent_round_label.config(text=f"本轮得分: {self.opponent_round_score}")
        
        if self.current_player == "player":
            self.selection_score_label.config(text=f"{self.current_selection_score}")
        else:
            # 如果是亨利回合，显示亨利的选择得分
            opponent_selection_score = self.calculate_opponent_selection_score()
            self.selection_score_label.config(text=f"{opponent_selection_score}")
        
        # 立即更新UI
        self.root.update()
    
    def update_buttons_state(self):
        """更新按钮状态"""
        if not self.game_in_progress:
            self.roll_button.config(state="disabled")
            self.end_turn_button.config(state="disabled")
            return
            
        if self.current_player == "player" and not self.opponent_is_playing:
            if self.awaiting_selection:
                # 检查当前选择是否有效
                valid_selection = self.current_selection_score > 0 and self.is_all_dice_scoring()
                
                if valid_selection:
                    # 有效选择，启用掷骰子和结束回合按钮
                    self.roll_button.config(state="normal")
                    self.end_turn_button.config(state="normal")
                    self.message_label.config(text="你可以继续掷骰子或结束回合")
                    self.has_valid_selection = True
                else:
                    # 无效选择，禁用掷骰子和结束回合按钮
                    self.roll_button.config(state="disabled")
                    self.end_turn_button.config(state="disabled")
                    self.message_label.config(text="请选择有效的得分骰子")
                    self.has_valid_selection = False
            else:
                if self.dice_rolled:
                    # 已经掷过骰子且完成选择，可以继续掷或结束回合
                    self.roll_button.config(state="normal")
                    self.end_turn_button.config(state="normal")
                    self.message_label.config(text="你可以继续掷骰子或结束回合")
                else:
                    # 回合开始，可以掷骰子
                    self.roll_button.config(state="normal")
                    self.end_turn_button.config(state="disabled")
                    self.message_label.config(text="点击掷骰子开始游戏")
        else:
            # 亨利回合或玩家回合但亨利正在执行操作，禁用所有按钮
            self.roll_button.config(state="disabled")
            self.end_turn_button.config(state="disabled")
            if self.opponent_is_playing:
                self.message_label.config(text="亨利回合")
        
        # 立即更新UI
        self.root.update()
    
    def is_all_dice_scoring(self):
        """检查是否所有选择的骰子都能得分"""
        if not self.player_selected_dice:
            return False
            
        # 获取选中的骰子值
        selected_values = [self.player_dice[i] for i in self.player_selected_dice]
        selected_values_sorted = sorted(selected_values)
        
        # 检查特殊组合 - 顺子
        if selected_values_sorted == [1, 2, 3, 4, 5, 6] and len(selected_values) == 6:
            return True
            
        # 检查特殊组合 - 12345 小顺子
        if selected_values_sorted == [1, 2, 3, 4, 5] and len(selected_values) == 5:
            return True
            
        # 检查特殊组合 - 23456 小顺子
        if selected_values_sorted == [2, 3, 4, 5, 6] and len(selected_values) == 5:
            return True
            
        # 检查特殊组合 - 三对
        counter = Counter(selected_values)
        if len(counter) == 3 and all(count == 2 for count in counter.values()) and len(selected_values) == 6:
            return True
            
        # 检查每个骰子是否能得分
        can_score = True
        
        # 检查三个或更多相同的骰子
        triples_found = {}  # 记录已经找到的三连
        
        for num, count in counter.items():
            if count >= 3:
                triples_found[num] = count // 3
        
        # 对于每个骰子，检查它是否能得分
        for value in selected_values:
            # 如果是1或5，它总是能得分
            if value == 1 or value == 5:
                continue
                
            # 如果它属于一个三连，且还有剩余的三连计数，则它能得分
            if value in triples_found and triples_found[value] > 0:
                triples_found[value] -= 1/3  # 扣减1/3，因为三连中的每个骰子都会检查
                continue
                
            # 如果都不是，则这个骰子不能得分
            can_score = False
            break
            
        return can_score
    
    def toggle_dice_selection(self, idx):
        """选择或取消选择骰子"""
        # 如果游戏未进行或者亨利正在进行回合，不允许操作
        if not self.game_in_progress or self.opponent_is_playing:
            return
            
        if not self.awaiting_selection or idx in self.player_locked_dice:
            return
            
        # 确保骰子在可选状态
        if self.current_player != "player":
            return
            
        # 检查是否已经选中，如果选中则取消，否则添加到选中列表
        if idx in self.player_selected_dice:
            self.player_selected_dice.remove(idx)
            # 更改按钮外观 - 取消选中
            self.player_dice_buttons[idx].config(bg="#4A7554", fg="white")
        else:
            self.player_selected_dice.append(idx)
            # 更改按钮外观 - 选中
            self.player_dice_buttons[idx].config(bg="#FFD700", fg="black")
        
        # 计算当前选择的得分
        self.calculate_selection_score()
        
        # 更新显示
        self.update_score_display()
        self.update_buttons_state()
    
    def is_valid_selection(self):
        """检查当前选择是否有效"""
        if not self.player_selected_dice:
            return False
            
        # 获取选中的骰子值
        selected_values = [self.player_dice[i] for i in self.player_selected_dice]
        selected_values_sorted = sorted(selected_values)
        
        # 检查是否是顺子 (1-2-3-4-5-6)
        if selected_values_sorted == [1, 2, 3, 4, 5, 6] and len(selected_values) == 6:
            return True
            
        # 检查是否是小顺子 (1-2-3-4-5)
        if selected_values_sorted == [1, 2, 3, 4, 5] and len(selected_values) == 5:
            return True
            
        # 检查是否是小顺子 (2-3-4-5-6)
        if selected_values_sorted == [2, 3, 4, 5, 6] and len(selected_values) == 5:
            return True
            
        # 检查是否有三对
        counter = Counter(selected_values)
        if len(counter) == 3 and all(count == 2 for count in counter.values()) and len(selected_values) == 6:
            return True
            
        # 单个1或5总是有效的
        if 1 in counter or 5 in counter:
            return True
            
        # 三个或更多相同的骰子
        for num, count in counter.items():
            if count >= 3:
                return True
        
        return False
    
    def calculate_selection_score(self):
        """计算当前选择的得分"""
        if not self.player_selected_dice:
            self.current_selection_score = 0
            return
            
        # 获取选中的骰子值
        selected_values = [self.player_dice[i] for i in self.player_selected_dice]
        selected_values_sorted = sorted(selected_values)
        
        # 计算得分
        score = 0
        
        # 计算每个数字出现的次数
        counter = Counter(selected_values)
        
        # 检查特殊组合 - 顺子
        if selected_values_sorted == [1, 2, 3, 4, 5, 6] and len(selected_values) == 6:
            score = 1500
            
        # 检查特殊组合 - 12345 小顺子
        elif selected_values_sorted == [1, 2, 3, 4, 5] and len(selected_values) == 5:
            score = 500
            
        # 检查特殊组合 - 23456 小顺子
        elif selected_values_sorted == [2, 3, 4, 5, 6] and len(selected_values) == 5:
            score = 750
            
        # 检查特殊组合 - 三对
        elif len(counter) == 3 and all(count == 2 for count in counter.values()) and len(selected_values) == 6:
            score = 1500
            
        else:
            # 处理常规组合
            for num, count in counter.items():
                # 处理三个或更多相同的骰子 - 修正计分规则
                if count >= 3:
                    # 计算基础分数
                    base_score = 0
                    if num == 1:
                        base_score = 1000
                    else:
                        base_score = num * 100
                    
                    # 计算额外骰子带来的翻倍
                    extra_dice = count - 3
                    multiplier = 2 ** extra_dice  # 每多一颗骰子，分数翻倍
                    
                    score += base_score * multiplier
                    
                    # 不再有单独计算剩余骰子的部分，因为所有相同的骰子都计入组合
                else:
                    # 处理单独的1和5
                    if num == 1:
                        score += count * 100
                    elif num == 5:
                        score += count * 50
        
        # 如果有不计分的骰子，总分应该为0
        if not self.is_all_dice_scoring():
            score = 0
            
        self.current_selection_score = score
    
    def calculate_opponent_selection_score(self):
        """计算亨利当前选择的得分"""
        if not self.opponent_selected_dice:
            return 0
            
        # 获取选中的骰子值
        selected_values = [self.opponent_dice[i] for i in self.opponent_selected_dice]
        selected_values_sorted = sorted(selected_values)
        
        # 计算得分
        score = 0
        
        # 计算每个数字出现的次数
        counter = Counter(selected_values)
        
        # 检查特殊组合 - 顺子
        if selected_values_sorted == [1, 2, 3, 4, 5, 6] and len(selected_values) == 6:
            score = 1500
            
        # 检查特殊组合 - 12345 小顺子
        elif selected_values_sorted == [1, 2, 3, 4, 5] and len(selected_values) == 5:
            score = 500
            
        # 检查特殊组合 - 23456 小顺子
        elif selected_values_sorted == [2, 3, 4, 5, 6] and len(selected_values) == 5:
            score = 750
            
        # 检查特殊组合 - 三对
        elif len(counter) == 3 and all(count == 2 for count in counter.values()) and len(selected_values) == 6:
            score = 1500
            
        else:
            # 处理常规组合
            for num, count in counter.items():
                # 处理三个或更多相同的骰子 - 修正计分规则
                if count >= 3:
                    # 计算基础分数
                    base_score = 0
                    if num == 1:
                        base_score = 1000
                    else:
                        base_score = num * 100
                    
                    # 计算额外骰子带来的翻倍
                    extra_dice = count - 3
                    multiplier = 2 ** extra_dice  # 每多一颗骰子，分数翻倍
                    
                    score += base_score * multiplier
                    
                    # 不再有单独计算剩余骰子的部分，因为所有相同的骰子都计入组合
                else:
                    # 处理单独的1和5
                    if num == 1:
                        score += count * 100
                    elif num == 5:
                        score += count * 50
            
        return score
    
    def apply_selection(self):
        """应用当前选择，锁定骰子并计分"""
        if not self.player_selected_dice:
            return False
            
        if self.current_selection_score <= 0:
            return False
            
        # 更新回合得分
        self.player_round_score += self.current_selection_score
        
        # 标记所选骰子为锁定状态
        for idx in self.player_selected_dice:
            self.player_locked_dice.append(idx)
        
        # 清空当前选择
        self.player_selected_dice = []
        self.current_selection_score = 0
        self.has_valid_selection = False
        
        # 更新状态
        self.awaiting_selection = False
        
        # 更新显示
        self.update_score_display()
        self.update_dice_display()
        
        # 检查是否所有骰子都已锁定
        if len(self.player_locked_dice) == 6:
            messagebox.showinfo("全部得分", "所有骰子都已得分！你获得了额外的掷骰机会。")
            self.player_locked_dice = []  # 解锁所有骰子
            self.update_dice_display()
        
        return True
    
    def apply_opponent_selection(self):
        """应用亨利选择，锁定骰子并计分"""
        if not self.opponent_selected_dice:
            return False
            
        # 计算选择得分
        score = self.calculate_opponent_selection_score()
        if score <= 0:
            return False
            
        # 更新亨利回合得分
        self.opponent_round_score += score
        
        # 标记所选骰子为锁定状态
        for idx in self.opponent_selected_dice:
            self.opponent_locked_dice.append(idx)
        
        # 清空当前选择
        self.opponent_selected_dice = []
        
        # 更新显示
        self.update_score_display()
        self.update_dice_display()
        
        # 检查是否所有骰子都已锁定
        if len(self.opponent_locked_dice) == 6:
            self.message_label.config(text="亨利骰子全部得分，获得额外掷骰机会")
            self.opponent_locked_dice = []  # 解锁所有骰子
            self.update_dice_display()
            self.root.update()
        
        return True
    
    def check_scoring_combinations(self, player="current"):
        """检查当前骰子中是否有可得分的组合"""
        # 获取未锁定的骰子值
        if player == "current":
            player = self.current_player
            
        if player == "player":
            unlocked_indices = [i for i in range(6) if i not in self.player_locked_dice]
            unlocked_values = [self.player_dice[i] for i in unlocked_indices]
        else:
            unlocked_indices = [i for i in range(6) if i not in self.opponent_locked_dice]
            unlocked_values = [self.opponent_dice[i] for i in unlocked_indices]
        
        # 检查单个1或5 - 这些总是可以得分的
        if 1 in unlocked_values or 5 in unlocked_values:
            return True
        
        # 检查三个或更多相同数字
        counter = Counter(unlocked_values)
        for count in counter.values():
            if count >= 3:
                return True
        
        # 检查是否是顺子
        if sorted(unlocked_values) == [1, 2, 3, 4, 5, 6] and len(unlocked_values) == 6:
            return True
        
        # 检查是否是小顺子 (1-2-3-4-5)
        if sorted(unlocked_values) == [1, 2, 3, 4, 5] and len(unlocked_values) == 5:
            return True
            
        # 检查是否是小顺子 (2-3-4-5-6)
        if sorted(unlocked_values) == [2, 3, 4, 5, 6] and len(unlocked_values) == 5:
            return True
        
        # 检查是否有三对
        if len(counter) == 3 and all(count == 2 for count in counter.values()) and len(unlocked_values) == 6:
            return True
        
        # 没有可得分组合
        return False
    
    def roll_dice(self):
        """掷骰子"""
        # 检查是否可以操作
        if not self.game_in_progress or self.opponent_is_playing or self.current_player != "player":
            return
            
        # 如果有有效的待选择得分，先应用它们
        if self.has_valid_selection:
            self.apply_selection()
        
        self.roll_button.config(state="disabled")
        self.end_turn_button.config(state="disabled")
        
        # 掷非锁定的骰子
        for i in range(6):
            if i not in self.player_locked_dice:
                self.player_dice[i] = random.randint(1, 6)
        
        self.dice_rolled = True
        self.update_dice_display()
        
        # 检查是否有可得分组合
        if self.check_scoring_combinations():
            self.awaiting_selection = True
            self.has_valid_selection = False
            # 启用骰子选择
            for i in range(6):
                if i not in self.player_locked_dice and self.current_player == "player":
                    self.player_dice_buttons[i].config(state="normal")
            self.message_label.config(text="请选择得分骰子")
        else:
            # 没有可得分组合，回合失败
            self.bust()
        
        self.update_buttons_state()
    
    def bust(self):
        """回合失败，得分清零并交换玩家"""
        if self.current_player == "player":
            self.player_round_score = 0
            messagebox.showinfo("哎呀！", "没有可得分的组合，本回合得分清零！")
        else:
            self.opponent_round_score = 0
            self.message_label.config(text="亨利没有可得分的组合，回合得分清零")
            self.root.update()
            time.sleep(1)
        
        self.switch_player()
    
    def end_turn(self):
        """结束当前回合，累加得分并交换玩家"""
        # 检查是否可以操作
        if not self.game_in_progress or self.opponent_is_playing or self.current_player != "player":
            return
            
        # 如果有有效的待选择得分，先应用它们
        if self.has_valid_selection:
            self.apply_selection()
            
        # 更新玩家总分
        self.player_score += self.player_round_score
        self.player_round_score = 0
            
        # 检查是否有玩家胜利
        if self.player_score >= self.WINNING_SCORE:
            self.game_over("玩家")
            return
        
        # 交换玩家
        self.switch_player()
    
    def game_over(self, winner):
        """游戏结束"""
        self.game_in_progress = False
        
        # 禁用所有按钮
        self.roll_button.config(state="disabled")
        self.end_turn_button.config(state="disabled")
        for button in self.player_dice_buttons:
            button.config(state="disabled")
        
        # 显示胜利信息
        self.message_label.config(text=f"游戏结束！{winner}获胜！")
        messagebox.showinfo("游戏结束", f"{winner}达到{self.WINNING_SCORE}分获胜！")
        
        # 询问是否重新开始
        if messagebox.askyesno("游戏结束", "是否要开始新游戏？"):
            self.reset_game()
    
    def reset_game(self):
        """重置游戏"""
        # 重置分数
        self.player_score = 0
        self.player_round_score = 0
        self.opponent_score = 0
        self.opponent_round_score = 0
        
        # 重置骰子状态
        self.player_dice = [1, 1, 1, 1, 1, 1]
        self.opponent_dice = [1, 1, 1, 1, 1, 1]
        self.player_selected_dice = []
        self.player_locked_dice = []
        self.opponent_locked_dice = []
        self.opponent_selected_dice = []
        
        # 重置游戏状态
        self.current_player = "player"
        self.dice_rolled = False
        self.awaiting_selection = False
        self.has_valid_selection = False
        self.game_in_progress = True
        self.opponent_is_playing = False
        
        # 更新显示
        self.update_dice_display()
        self.update_score_display()
        self.update_buttons_state()
        
        self.message_label.config(text="新游戏开始，点击掷骰子开始")
    
    def switch_player(self):
        """交换当前玩家"""
        if self.current_player == "player":
            self.current_player = "opponent"
            
            # 解锁玩家下一回合的骰子
            self.player_locked_dice = []
            
            # 设置标志，防止玩家操作
            self.opponent_is_playing = True
            
            # 更新显示
            self.update_dice_display()
            self.update_score_display()
            self.update_buttons_state()
            
            # 启动AI亨利线程
            self.message_label.config(text="亨利回合开始")
            # 使用线程避免UI冻结
            threading.Thread(target=self.opponent_turn, daemon=True).start()
        else:
            self.current_player = "player"
            
            # 解锁亨利下一回合的骰子
            self.opponent_locked_dice = []
            
            # 重置亨利操作标志
            self.opponent_is_playing = False
            
            # 重置回合状态
            self.dice_rolled = False
            self.awaiting_selection = False
            self.player_selected_dice = []
            self.current_selection_score = 0
            self.has_valid_selection = False
            
            # 更新显示
            self.update_dice_display()
            self.update_score_display()
            self.update_buttons_state()
            
            self.message_label.config(text="你的回合开始")
    
    def opponent_turn(self):
        """AI亨利的回合"""
        try:
            if not self.game_in_progress:
                return
                
            # 重置亨利状态
            self.opponent_locked_dice = []
            self.opponent_selected_dice = []
            
            # 延迟执行，让玩家看到亨利回合开始
            time.sleep(1)
            
            # 亨利掷骰子
            self.opponent_roll_dice()
            
            # 亨利回合结束，累加得分
            self.opponent_score += self.opponent_round_score
            self.opponent_round_score = 0
            
            # 检查亨利是否胜利
            if self.opponent_score >= self.WINNING_SCORE:
                self.update_score_display()
                self.game_over("亨利")
                return
            
            # 更新显示
            self.update_score_display()
            
            # 切换回玩家回合
            time.sleep(1)
            self.message_label.config(text="亨利回合结束")
            time.sleep(1)
            
            # 在主线程安全地切换玩家
            self.root.after(0, self.switch_to_player)
            
        except Exception as e:
            print(f"亨利回合发生错误: {e}")
            # 确保在发生错误时也能切换回玩家回合
            self.root.after(0, self.switch_to_player)
    
    def switch_to_player(self):
        """安全地切换到玩家回合"""
        self.current_player = "player"
        self.opponent_is_playing = False
        
        # 解锁亨利下一回合的骰子
        self.opponent_locked_dice = []
        
        # 重置回合状态
        self.dice_rolled = False
        self.awaiting_selection = False
        self.player_selected_dice = []
        self.current_selection_score = 0
        self.has_valid_selection = False
        
        # 更新显示
        self.update_dice_display()
        self.update_score_display()
        self.update_buttons_state()
        
        self.message_label.config(text="你的回合开始")
    
    def opponent_roll_dice(self):
        """亨利掷骰子"""
        if not self.game_in_progress or not self.opponent_is_playing:
            return
            
        self.message_label.config(text="亨利掷骰子")
        self.root.update()
        
        # 延迟
        time.sleep(1)
        
        # 掷非锁定的骰子
        for i in range(6):
            if i not in self.opponent_locked_dice:
                self.opponent_dice[i] = random.randint(1, 6)
        
        self.update_dice_display()
        
        # 延迟
        time.sleep(0.5)
        
        # 检查是否有可得分组合
        if self.check_scoring_combinations("opponent"):
            self.message_label.config(text="亨利选择得分骰子")
            self.root.update()
            time.sleep(1)
            self.opponent_select_dice()
        else:
            # 没有可得分组合，回合失败
            self.opponent_round_score = 0
            self.message_label.config(text="亨利没有可得分的组合，回合得分清零")
            self.root.update()
            time.sleep(2)
            
            # 回合结束，不进行更多操作，让opponent_turn处理切换回玩家回合
            return
    
    def opponent_select_dice(self):
        """亨利选择得分骰子"""
        if not self.game_in_progress or not self.opponent_is_playing:
            return
            
        # 优先选择最高得分的组合
        self.opponent_selected_dice = []
        
        # 获取未锁定的骰子索引
        unlocked_indices = [i for i in range(6) if i not in self.opponent_locked_dice]
        
        # 尝试获取最佳选择
        best_selection = self.get_best_opponent_selection(unlocked_indices)
        self.opponent_selected_dice = best_selection
        
        # 高亮显示选中的骰子
        self.update_dice_display()
        self.update_score_display()
        self.root.update()
        
        # 延迟一下让玩家看到选择
        time.sleep(2)
        
        # 应用选择
        selection_score = self.calculate_opponent_selection_score()
        if selection_score > 0:
            self.message_label.config(text=f"亨利选择得分: {selection_score}")
            self.apply_opponent_selection()
            
            # 延迟
            time.sleep(1)
            
            # 决定是否继续掷骰子
            if self.opponent_decide_continue():
                self.message_label.config(text="亨利继续掷骰子")
                self.root.update()
                time.sleep(1)
                self.opponent_roll_dice()
            else:
                self.message_label.config(text="亨利结束回合")
                self.root.update()
                time.sleep(1)
                # 回合结束，让opponent_turn处理切换回玩家回合
                return
        else:
            self.message_label.config(text="亨利选择无效")
            self.root.update()
            time.sleep(1)
            self.opponent_select_dice()  # 重新选择
    
    def get_best_opponent_selection(self, available_indices):
        """获取亨利的最佳选择"""
        if not available_indices:
            return []
            
        # 获取骰子值
        available_values = [self.opponent_dice[i] for i in available_indices]
        available_values_sorted = sorted(available_values)
        
        # 检查特殊组合
        # 检查顺子
        if available_values_sorted == [1, 2, 3, 4, 5, 6]:
            return available_indices  # 返回所有骰子
            
        # 检查小顺子 (1-2-3-4-5)
        if available_values_sorted == [1, 2, 3, 4, 5] and len(available_values) == 5:
            return available_indices  # 返回所有骰子
            
        # 检查小顺子 (2-3-4-5-6)
        if available_values_sorted == [2, 3, 4, 5, 6] and len(available_values) == 5:
            return available_indices  # 返回所有骰子
            
        # 检查三对
        counter = Counter(available_values)
        if len(counter) == 3 and all(count == 2 for count in counter.values()):
            return available_indices  # 返回所有骰子
        
        # 尝试找最大得分的组合
        best_score = 0
        best_selection = []
        
        # 优先选择三个或更多相同的骰子
        for num, count in counter.items():
            if count >= 3:
                # 找出这些骰子的索引
                indices = [idx for idx in available_indices if self.opponent_dice[idx] == num]
                
                # 计算得分
                if num == 1:
                    score = 1000 * (2 ** (count - 3))
                else:
                    score = (num * 100) * (2 ** (count - 3))
                
                if score > best_score:
                    best_score = score
                    best_selection = indices
        
        # 如果没有找到三个或更多相同的，选择所有的1和5
        if not best_selection:
            # 找出所有的1
            ones_indices = [idx for idx in available_indices if self.opponent_dice[idx] == 1]
            if ones_indices:
                best_selection = ones_indices
                best_score = len(ones_indices) * 100
                
            # 如果没有1，找出所有的5
            if not best_selection:
                fives_indices = [idx for idx in available_indices if self.opponent_dice[idx] == 5]
                if fives_indices:
                    best_selection = fives_indices
                    best_score = len(fives_indices) * 50
            
            # 如果既有1又有5，选择得分最高的组合
            if counter.get(1, 0) > 0 and counter.get(5, 0) > 0:
                ones_score = counter[1] * 100
                fives_score = counter[5] * 50
                
                if ones_score + fives_score > best_score:
                    ones_indices = [idx for idx in available_indices if self.opponent_dice[idx] == 1]
                    fives_indices = [idx for idx in available_indices if self.opponent_dice[idx] == 5]
                    best_selection = ones_indices + fives_indices
                    best_score = ones_score + fives_score
        
        return best_selection
    
    def opponent_decide_continue(self):
        """亨利决定是否继续掷骰子"""
        # 计算继续掷骰子的风险和收益
        
        # 计算当前回合得分
        current_round_score = self.opponent_round_score
        
        # 计算还有多少未锁定的骰子
        remaining_dice = 6 - len(self.opponent_locked_dice)
        
        # 如果所有骰子都已锁定，总是继续掷（因为会重置所有骰子）
        if remaining_dice == 0:
            return True
            
        # 如果回合得分很高，谨慎行事
        if current_round_score > 1000:
            # 高得分情况下，降低继续的概率
            risk_factor = 0.4
        elif current_round_score > 500:
            # 中等得分
            risk_factor = 0.6
        else:
            # 低得分，大胆一些
            risk_factor = self.ai_risk_factor
        
        # 根据剩余骰子数调整风险因子
        # 骰子越少，得分机会越低，风险越高
        if remaining_dice <= 2:
            risk_factor *= 0.7
        elif remaining_dice <= 4:
            risk_factor *= 0.85
            
        # 如果当前轮次分数加上总分接近胜利，提高继续概率
        if (self.opponent_score + current_round_score) >= self.WINNING_SCORE * 0.8:
            risk_factor += 0.2
            
        # 随机决定
        return random.random() < risk_factor

# 创建并运行应用
def main():
    root = tk.Tk()
    game = KingdomComeDiceGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()