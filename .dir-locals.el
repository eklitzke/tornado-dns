((nil . ((indent-tabs-mode . nil)
		 (tab-width . 4)
         (compile-command . "cd $(git rev-parse --show-cdup | sed 's/^$/./') && scons")
		 (fill-column . 80)))
 
 (python-mode . ((tab-width . 4)
				 (indent-tabs-mode . nil)
				 (python-indent . 4))))
