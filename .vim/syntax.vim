" Usage: copy this file into .vim (or .nvim)/syntax and rename it to "radon.vim"
" Do the same for "ftdetect.vim" but move it to .nvim/ftdetect instead

if exists("b:current_syntax")
    finish
endif

syntax keyword radonKW var and or not if elif else for to step while fun return
syntax keyword radonKW continue break class include try catch as in
syntax keyword radonKW null false true
highlight link radonKW Keyword

syntax keyword radonBuiltinFunc print print_ret input input_int clear cls require exit
syntax keyword radonBuiltinFunc is_num is_int is_float is_str is_bool is_array is_fun
syntax keyword radonBuiltinFunc arr_append arr_pop arr_extend arr_find arr_slice arr_len arr_chunk arr_get
syntax keyword radonBuiltinFunc str_len str_slice str_find str_get
syntax keyword radonBuiltinFunc int float str bool type
syntax keyword radonBuiltinFunc pyapi
syntax keyword radonBuiltinFunc require exit sys_args time_now
highlight link radonBuiltinFunc Function

syntax match radonComment "\v#.*$"
highlight link radonComment Comment

syntax match radonOp /==/
syntax match radonOp /!=/
syntax match radonOp /</
syntax match radonOp />/
syntax match radonOp /<=/
syntax match radonOp />=/
syntax match radonOp /+=/
syntax match radonOp /-=/
syntax match radonOp /*=/
syntax match radonOp "/="
syntax match radonOp "//"
syntax match radonOp "%="
syntax match radonOp "\^="
syntax match radonOp /+/
syntax match radonOp /-/
syntax match radonOp /\*/
syntax match radonOp "/"
syntax match radonOp "\^"
syntax match radonOp "%"
syntax match radonOp "("
syntax match radonOp ")"
syntax match radonOp "{"
syntax match radonOp "}"
syntax match radonOp /\[/
syntax match radonOp /\]/
syntax match radonOp "="
highlight link radonOp Operator

syntax match radonNum /\d\+/
highlight link radonNum Number

syntax region radonString start=/\v"/ skip=/\v\\./ end=/\v"/
highlight link radonString String

let b:current_syntax = "radon"
