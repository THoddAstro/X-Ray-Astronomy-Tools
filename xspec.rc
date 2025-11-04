# Start logging
log >/home/thodd/xspec_logs/xspec_2025-11-04.log

# Plot window
cpd /xs

# Load files
load /disc30/common-files/relxill_tables_v2.6/source/librelxill.so

# Rounding proc
proc sigfig {value sigfigs} {
    # If zero, return zero
    if {$value == 0} {
        return 0
    }

    set mag [expr {floor( log(abs($value)) / log(10) )}]
    set scale [expr {pow(10.0, $mag - ($sigfigs - 1))}]

    set rounded [expr {round($value / $scale) * $scale}]
    return $rounded
}

# Steppar Proc
proc stp {par_index start stop {steps 50} {par_index2 "None"} {start2 "None"} {stop2 "None"} {steps2 50}} {
    
    # Delete previous steppar save all   
    if {[file exists before_steppar.xcm]} {
        catch {file delete before_steppar.xcm}
    }

    # Save state
    save all before_steppar
    puts "Saved current state to before_steppar.xcm"

    # Do 1D or 2D steppar
    if {$par_index2 == "None"} {
        steppar best $par_index $start $stop $steps
    } else {
        steppar best $par_index $start $stop $steps $par_index2 $start2 $stop2 $steps2
    }

    # Collect cstat and par1 values
    tclout steppar statistic
    set stat $xspec_tclout
    tclout steppar $par_index
    set par1 $xspec_tclout
    tclout pinfo $par_index
    set par1name $xspec_tclout

    # Collect par2 values
    if {$par_index2 != "None"} {
        tclout steppar $par_index2
        set par2 $xspec_tclout
        tclout pinfo $par_index2
        set par2name $xspec_tclout
    } else {
        set par2 "No second parameter - 1D steppar"
        set par2name "!"
    }

    # Write to files
    set par_separator " - "

    set f [open "steppar_cstat.dat" w]
    puts $f $stat
    close $f

    set f [open "steppar_par1.dat" w]
    puts $f $par_index$par_separator$par1name\n$par1
    close $f

    set f [open "steppar_par2.dat" w]
    puts $f $par_index2$par_separator$par2name\n$par2
    close $f

    puts "Written steppar values to files"

    # Run Python script
    set cwd [file normalize .]
    set cmd [concat python3 " /home/thodd/Masters/plotSteppar.py " $cwd]
    eval exec $cmd
    puts "Plot generated successfully"
    }

# AIC/BIC Proc
proc abc {} {
    # Get fit statistic
    tclout stat
    set fit_stat $xspec_tclout
    tclout dof
    set n_bins [lindex $xspec_tclout  1]

    # Get number of model parameters
    tclout modpar
    set pars $xspec_tclout

    # Get number of free parameters
    set free_params 0
    for {set i 1} {$i < $pars + 1} {incr i} {
        tclout pfree $i
        if {$xspec_tclout == "T"} {
            set free_params [expr $free_params + 1]
        }
    }
    # Calculate AIC
    puts [concat "AIC: " [format "%.3f" [expr 2 * $free_params + $fit_stat]] ", $free_params free parameters"]

    # Calculate BIC
    puts [concat "BIC: " [format "%.3f" [expr $free_params * log($n_bins) + $fit_stat]] ", $free_params free parameters, $n_bins bins."]
    }

# Corner plot proc
proc corner {fits_file args} {
    # Get number of model parameters
    tclout modpar
    set pars $xspec_tclout

    # Get list to map free parameter numbers with parameters
    set free_params " "
    set free_count 1
    for {set i 1} {$i < $pars + 1} {incr i} {
        tclout pfree $i
        if {$xspec_tclout == "T"} {
            append free_params " " $free_count
            incr free_count
        } else {
            append free_params " " "N"
        }
    }

    # Run Python script
    set cwd [file normalize .]
    set cmd [concat python3 " /home/thodd/Masters/plotMCMC.py " $cwd $fits_file [list $free_params] $args]
    eval exec $cmd
    # set result [eval exec $cmd]
    # puts $result
    puts "Plot generated successfully"
    }

# Get errors
proc geterr {{latex 0}} {
    # Get number of model parameters
    tclout modpar
    set pars $xspec_tclout

    # For each free parameter
    for {set i 1} {$i < $pars + 1} {incr i} {
        tclout pfree $i
        if {$xspec_tclout == "T"} {
            tclout param $i
            set par_val [lindex $xspec_tclout  0]
            tclout error $i
            set par_range [split $xspec_tclout]
            set par_err_lo [expr {$par_val - [lindex $par_range 0]}]
            set par_err_hi [expr {[lindex $par_range 1] - $par_val}]
            tclout pinfo $i
            set name $xspec_tclout

            # Rounding
            set par_val [sigfig $par_val 3]
            set par_err_lo [sigfig $par_err_lo 2]
            set par_err_hi [sigfig $par_err_hi 2]

            if {$latex == 0} {
                puts [format "%d - %-10s: %12.5f  (-%12.5f , +%12.5f)" $i $name $par_val $par_err_lo $par_err_hi]
            } elseif {$latex == 1} {
                puts "$i - $name:"
                puts "$$par_val\\err{$par_err_lo}{$par_err_hi}$"
            } elseif {$latex == 2} {
                set par_err_lo [expr {abs($par_err_lo)}]
                puts "$i - $name:"
                puts "$par_val: ($par_err_lo, $par_err_hi)"
            }
        }
    }
}

# Notice/ignore data
interp alias {} na {} notice all
interp alias {} usp412 {} {notice all; ignore **:0.0-.4 12.-**}
interp alias {} usp310 {} {notice all; ignore **:0.0-.3 10.-**}
interp alias {} us210 {} {notice all; ignore **:0.0-2. 10.-**}
interp alias {} us510 {} {notice all; ignore **:0.0-5. 10.-**}
interp alias {} rgslim {} {setplot w; ignore **-7. 30.-**; setplot e}

# Plotting
interp alias {} pld {} pl ld
interp alias {} pldr {} pl ld ra
interp alias {} plm {} pl mo
interp alias {} re20 {} setplot re 20 10 -1

# Show
interp alias {} sp {} show par
interp alias {} sf {} show free
interp alias {} ss {} show fit

# MCMC
interp alias {} mcinit {} {chain type gw; chain proposal gaussian fit; chain walkers 20; chain length 200000; parallel walkers 4; chain burn 100000}
interp alias {} chbu {} chain burn
interp alias {} chle {} chain length
interp alias {} chwa {} chain walkers
interp alias {} pawa {} parallel walkers
interp alias {} chlo {} chain load
interp alias {} chcl {} chain clear
interp alias {} chru {} chain run

# Misc
interp alias {} sa {} save all
interp alias {} np {} newpar
interp alias {} ptclo {} {puts $xspec_tclout}

# Initial commands
statistic cstat
setplot e
