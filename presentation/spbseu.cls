\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{spbseu}

\LoadClass[hyperref={unicode=true}]{beamer}


% Кириллица
\usepackage[utf8]{inputenc}
\usepackage[english, main=russian]{babel}


% Стиль презентации
\usetheme{Madrid}
\useoutertheme{shadow}
\usefonttheme{professionalfonts}

% Цвета презентации
\definecolor{spbseu}{rgb}{0,0.51176,0.54901}
\usecolortheme[named=spbseu]{structure}

% Отключение верхней и нижней линий
\setbeamertemplate{headline}{}
\setbeamertemplate{footline}{}

% Навигация
\addtobeamertemplate{navigation symbols}{}{%
    \usebeamerfont{footline}%
    \usebeamercolor[fg]{footline}%
    \hspace{1em}%
    \insertframenumber/\inserttotalframenumber
}

% Номер слайда
\beamersetuncovermixins{\opaqueness<1>{25}}{\opaqueness<2->{15}}

% Выравнивание
\usepackage{ragged2e} 
\apptocmd{\frame}{}{\justifying}{}
