vim.opt.expandtab = true
vim.opt.tabstop=2
vim.opt.softtabstop=2
vim.opt.shiftwidth=2

vim.opt.swapfile = false

vim.opt.nu = true
vim.opt.relativenumber = true

vim.opt.colorcolumn = "0"
vim.opt.signcolumn = "yes"

vim.api.nvim_create_autocmd("TextYankPost", {
    desc = "Highlight when yanking (copying) text",
    callback = function()
        vim.hl.on_yank()
    end,
})
