LATEX_COVER_LETTER_TEMPLATE = """
\\documentclass[11pt,a4paper,roman]{{moderncv}}      
\\usepackage[english]{{babel}}
\\usepackage{{ragged2e}}
\\usepackage{{float}}
\\usepackage{{graphicx}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{lipsum}} % dummy texts package

\\moderncvstyle{{classic}}                            
\\moderncvcolor{{green}} % Bullet point color                          

% Page margins
\\usepackage[scale=0.81]{{geometry}} % Page margins

% Your Information, please revise
\\name{{Ankith Savio}}{{Arogya Dass}}
\\address{{269 Dawlish Rd}}{{Selly Oak, Birmingham}}{{B29 7AU}}
\\phone{{+44 7435751747}}                   
\\email{{ankithsavio@gmail.com}}             

% --- Define Content Commands (Variables) ---
\\newcommand{{\\recipientName}}{{{recipient_name}}}
\\newcommand{{\\coverLetterContent}}{{
  {content}
}}
% --- End of Content Commands ---

\\begin{{document}}

% Imperial College Logo
% ref: https://orama.tv/imperial-college-london-logo/
\\begin{{minipage}}[t]{{\\textwidth}}
% \\includegraphics[width=0.35\\textwidth]{{logo.png}}
\\end{{minipage}}

\\recipient{{Dear \\recipientName,}}{{}}  % Use the command here
\\opening{{\\vspace*{{-2em}}}}
\\closing{{Sincerely,}}{{\\vspace*{{-2em}}}}  
\\makelettertitle
\\justifying

\\coverLetterContent % Insert the content here

\\vspace*{{2em}}
Sincerely,

\\textbf{{Ankith Savio Arogya Dass}}

% \\lipsum[2-5] % feel free to remove this dummy texts

% \\makeletterclosing

\\end{{document}}
"""
