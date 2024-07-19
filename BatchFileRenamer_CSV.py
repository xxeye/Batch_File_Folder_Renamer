import os
import shutil
import csv
import tkinter as tk
import time
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from collections import Counter

# 初始化一個緩存來存儲已檢查過的文件和目錄資訊
checked_dirs = set()

def select_path(var, mode='file', filetypes=[("CSV 文件", "*.csv")]):
    initial_dir = var.get() if var.get() else None
    if mode == 'file':
        path = filedialog.askopenfilename(filetypes=filetypes, initialdir=initial_dir)
    elif mode == 'directory':
        path = filedialog.askdirectory(initialdir=initial_dir)
    if path:
        var.set(path)

def select_csv_file():
    select_path(csv_file_path, 'file', [("CSV 文件", "*.csv")])

def select_target_folder():
    select_path(target_folder_path, 'directory')

def select_complete_folder():
    select_path(complete_folder_path, 'directory')

def select_new_target_folder():
    select_path(new_target_folder_path, 'directory')

def add_row():
    row_frame = tk.Frame(scrollable_frame)
    row_frame.pack(fill='x', padx=5, pady=2)
    
    tk.Label(row_frame, text="更名字詞").pack(side='left', padx=5)
    tk.Entry(row_frame, width=20).pack(side='left', padx=5)
    
    tk.Label(row_frame, text="替換字詞").pack(side='left', padx=5)
    tk.Entry(row_frame, width=20).pack(side='left', padx=5)
    
    add_button = tk.Button(row_frame, text='+', command=add_row)
    add_button.pack(side='left', padx=5)
    
    if len(scrollable_frame.winfo_children()) > 2:
        remove_button = tk.Button(row_frame, text='-', command=lambda: remove_row(row_frame))
        remove_button.pack(side='left', padx=5)
    else:
        add_button.config(state='normal')

def remove_row(frame):
    frame.destroy()

def check_duplicates(rename_list):
    keys = [item[0] for item in rename_list]  # 提取所有的更名字詞
    values = [item[1] for item in rename_list if item[1]]  # 提取所有的非空替換字詞

    # 查找更名字詞中的重複條目
    duplicate_keys = sorted({key for key, count in Counter(keys).items() if count > 1})
    # 查找替換字詞中的重複條目
    duplicate_values = sorted({value for value, count in Counter(values).items() if count > 1})

    # 如果有重複的更名字詞或替換字詞，則生成錯誤信息
    if duplicate_keys or duplicate_values:
        error_message = "重複條目發現列表\n"
        if duplicate_keys:
            error_message += f"更名字詞中有重複: {', '.join(duplicate_keys)}\n"
        if duplicate_values:
            error_message += f"替換字詞中有重複: {', '.join(duplicate_values)}\n"

        return error_message  # 返回錯誤信息

    return None  # 如果沒有重複條目，返回 None


def show_error_message(error_message, continue_func):
    error_window = tk.Toplevel(root)
    error_window.title("錯誤")
    error_window.geometry("400x300")

    lbl = tk.Label(error_window, text="重複條目發現，可能會覆蓋檔案，是否繼續?", font=('Arial', 12))
    lbl.pack(pady=10)

    txt = ScrolledText(error_window, wrap=tk.WORD, width=50, height=10)
    txt.pack(pady=10)
    txt.insert(tk.END, error_message)
    txt.config(state=tk.DISABLED)

    btn_frame = tk.Frame(error_window)
    btn_frame.pack(pady=10)

    btn_continue = tk.Button(btn_frame, text="繼續", command=lambda: [error_window.destroy(), continue_func()])
    btn_continue.pack(side="left", padx=5)

    btn_cancel = tk.Button(btn_frame, text="取消", command=error_window.destroy)
    btn_cancel.pack(side="left", padx=5)

def move_and_rename_file(old_path, new_name, target_folder, complete_folder):
    relative_path = os.path.relpath(old_path, target_folder)
    new_dir = os.path.join(complete_folder, os.path.dirname(relative_path))

    # 使用緩存來檢查目錄是否存在
    if new_dir not in checked_dirs:
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        checked_dirs.add(new_dir)

    new_path = os.path.join(new_dir, new_name)
    shutil.move(old_path, new_path)

def process_files():
    csv_file = csv_file_path.get()
    target_folder = target_folder_path.get()
    complete_folder = complete_folder_path.get()

    if target_folder == complete_folder:
        messagebox.showerror("錯誤", "目標文件夾與完成文件夾不能相同")
        return
    
    if not csv_file and not any(row_frame.winfo_children() for row_frame in scrollable_frame.winfo_children()):
        messagebox.showerror("錯誤", "請選擇CSV文件或自行鍵入更名字詞和替換字詞")
        return
    
    if not target_folder or not complete_folder:
        messagebox.showerror("錯誤", "請選擇所有路徑")
        return
    
    rename_list = []
    if csv_file:
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rename_list = list(reader)
        if len(rename_list[0]) < 2:
            messagebox.showerror("錯誤", "CSV文件必須包含至少兩列")
            return
    
    for row_frame in scrollable_frame.winfo_children():
        entries = row_frame.winfo_children()
        if len(entries) >= 4:
            old_name = entries[1].get().strip()
            new_name = entries[3].get().strip()
            if old_name:
                rename_list.append([old_name, new_name])

    error_message = check_duplicates(rename_list)
    if error_message:
        show_error_message(error_message, lambda: process_files_with_confirmation(rename_list, target_folder, complete_folder))
        return

    process_files_with_confirmation(rename_list, target_folder, complete_folder)

def process_files_with_confirmation(rename_list, target_folder, complete_folder):
    global checked_dirs
    checked_dirs.clear()  # 清空緩存
    moved_files_count = 0
    rename_list = sorted(rename_list, key=lambda item: -len(item[0]))
    rename_dict = {item[0]: item[1] for item in rename_list}

    # 檢查 sorted_rename.csv 是否已存在，若存在則加上時間戳
    parent_directory = os.path.dirname(complete_folder)
    sorted_csv_path = os.path.join(parent_directory, "sorted_rename.csv")
    if os.path.exists(sorted_csv_path):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        sorted_csv_path = os.path.join(parent_directory, f"sorted_rename_{timestamp}.csv")

    with open(sorted_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["更名字詞", "替換字詞"])
        writer.writerows(rename_list)

    for old, new in rename_dict.items():
        for root, _, files in os.walk(target_folder):
            for file in files:
                if old in file:
                    original_path = os.path.join(root, file)
                    if new is None or new == '':
                        # 只移動文件，不重命名
                        new_name = file
                    else:
                        if rename_option.get() == "更改從頭部搜索的第一個字詞":
                            new_name = file.replace(old, new, 1)
                        elif rename_option.get() == "更改從尾部搜索的第一個字詞":
                            parts = file.rsplit(old, 1)
                            new_name = new.join(parts)
                        else:
                            new_name = None  # 如果沒有匹配到任何條件

                    if new_name:
                        move_and_rename_file(original_path, new_name, target_folder, complete_folder)
                        moved_files_count += 1

    complete_folder_files_count = sum([len(files) for _, _, files in os.walk(complete_folder)])
    messagebox.showinfo("信息", f"處理完成\n重命名或移動 {moved_files_count} 筆文件，完成文件夾內有 {complete_folder_files_count} 筆文件")

def load_folder_structure(folder):
    for i in tree.get_children():
        tree.delete(i)
    if folder:
        for root, dirs, files in os.walk(folder):
            for d in dirs:
                tree.insert('', 'end', text=os.path.relpath(os.path.join(root, d), folder), open=True)

def load_new_folder_structure(folder):
    # 僅在 folder 有值時才加載資料夾結構
    if not folder:
        return
    for i in tree.get_children():
        tree.delete(i)
    for root, dirs, files in os.walk(folder):
        for d in dirs:
            tree.insert('', 'end', text=os.path.relpath(os.path.join(root, d), folder), open=True)

def rename_folders():
    selected_folders = tree.selection()
    old_names = old_name_var.get().split(',')
    new_names = new_name_var.get().split(',')
    
    if len(old_names) != len(new_names):
        messagebox.showerror("錯誤", "更名字詞與替換字詞數量不匹配。")
        return
    
    rename_dict = {old_name: new_name for old_name, new_name in zip(old_names, new_names)}
    
    sorted_folders = sorted(selected_folders, key=lambda folder: len(tree.item(folder, 'text').split(os.sep)), reverse=True)
    
    for folder in sorted_folders:
        old_name = tree.item(folder, 'text')
        old_name_base = os.path.basename(old_name)
        if old_name_base in rename_dict:
            new_folder_name = rename_dict[old_name_base]
            if old_name_base == new_folder_name:
                continue
            full_old_path = os.path.join(new_target_folder_path.get(), old_name)
            new_relative_path = os.path.join(os.path.dirname(old_name), new_folder_name)
            full_new_path = os.path.join(new_target_folder_path.get(), new_relative_path)
            
            if os.path.exists(full_new_path):
                base, ext = os.path.splitext(new_folder_name)
                count = 1
                while os.path.exists(os.path.join(new_target_folder_path.get(), os.path.join(os.path.dirname(old_name), f"{base}_{count}{ext}"))):
                    count += 1
                full_new_path = os.path.join(new_target_folder_path.get(), os.path.join(os.path.dirname(old_name), f"{base}_{count}{ext}"))
            
            os.rename(full_old_path, full_new_path)
    
    load_new_folder_structure(new_target_folder_path.get())

root = tk.Tk()
root.title("文件重命名和移動工具")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

csv_file_path = tk.StringVar()
target_folder_path = tk.StringVar()
complete_folder_path = tk.StringVar()
new_target_folder_path = tk.StringVar()
rename_option = tk.StringVar(value="更改從尾部搜索的第一個字詞")

# 定義 on_new_target_folder_change 函數
def on_new_target_folder_change(*args):
    if new_target_folder_path.get():
        load_new_folder_structure(new_target_folder_path.get())

# 設置 new_target_folder_path trace
new_target_folder_path.trace_add("write", on_new_target_folder_change)

main_frame = tk.Frame(notebook)
notebook.add(main_frame, text='文件重命名和移動')

new_feature_frame = tk.Frame(notebook)
notebook.add(new_feature_frame, text='修改資料夾名稱')

tk.Label(main_frame, text="CSV 文件：").grid(row=0, column=0, padx=10, pady=5, sticky='e')
tk.Entry(main_frame, textvariable=csv_file_path, width=50).grid(row=0, column=1, padx=10, pady=5)
tk.Button(main_frame, text="瀏覽...", command=select_csv_file).grid(row=0, column=2, padx=10, pady=5)

tk.Label(main_frame, text="目標文件夾：").grid(row=1, column=0, padx=10, pady=5, sticky='e')
tk.Entry(main_frame, textvariable=target_folder_path, width=50).grid(row=1, column=1, padx=10, pady=5)
tk.Button(main_frame, text="瀏覽...", command=select_target_folder).grid(row=1, column=2, padx=10, pady=5)

tk.Label(main_frame, text="完成文件夾：").grid(row=2, column=0, padx=10, pady=5, sticky='e')
tk.Entry(main_frame, textvariable=complete_folder_path, width=50).grid(row=2, column=1, padx=10, pady=5)
tk.Button(main_frame, text="瀏覽...", command=select_complete_folder).grid(row=2, column=2, padx=10, pady=5)

tk.Label(main_frame, text="重命名規則：").grid(row=3, column=0, padx=10, pady=5, sticky='e')
combobox = ttk.Combobox(main_frame, textvariable=rename_option, values=["更改從頭部搜索的第一個字詞", "更改從尾部搜索的第一個字詞"], width=25)
combobox.grid(row=3, column=1, padx=10, pady=5)

frame = tk.Frame(main_frame)
frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky='ew')

canvas = tk.Canvas(frame, bd=1, relief="solid")
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

tip_label = tk.Label(scrollable_frame, text="提示：可以自行輸入條目，也可以與CSV文件同時使用。", fg='blue')
tip_label.pack(fill='x', padx=5, pady=5)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

add_row()

process_button = tk.Button(main_frame, text="處理", command=process_files)
process_button.grid(row=5, column=0, columnspan=3, padx=10, pady=20, sticky='ew')

main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)
main_frame.grid_columnconfigure(2, weight=1)
main_frame.grid_rowconfigure(5, weight=1)

tk.Label(new_feature_frame, text="目標文件夾：").pack(padx=10, pady=5)
tk.Entry(new_feature_frame, textvariable=new_target_folder_path, width=50).pack(padx=10, pady=5)
tk.Button(new_feature_frame, text="瀏覽...", command=select_new_target_folder).pack(padx=10, pady=5)

tree = ttk.Treeview(new_feature_frame, selectmode="extended")
tree.pack(fill='both', expand=True, padx=10, pady=5)

def on_folder_select(event):
    selected_folders = tree.selection()
    if selected_folders:
        old_names = [os.path.basename(tree.item(folder, 'text')) for folder in selected_folders]
        old_name_var.set(','.join(old_names))

tree.bind('<<TreeviewSelect>>', on_folder_select)

tk.Label(new_feature_frame, text="更名字詞，若選取多筆資料將以逗號分隔：").pack(padx=10, pady=5)
old_name_var = tk.StringVar()
tk.Label(new_feature_frame, textvariable=old_name_var, width=50, relief="sunken", anchor="w").pack(padx=10, pady=5, fill="x")

tk.Label(new_feature_frame, text="替換字詞，若選取多筆資料請以逗號分隔：").pack(padx=10, pady=5)
new_name_var = tk.StringVar()
tk.Entry(new_feature_frame, textvariable=new_name_var, width=50).pack(padx=10, pady=5)

rename_button = tk.Button(new_feature_frame, text="重命名", command=rename_folders)
rename_button.pack(padx=10, pady=20)

root.mainloop()
