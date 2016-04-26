#!/usr/bin/perl -w

# Copyright (C) 2015 The University of Notre Dame
# This software is distributed under the GNU General Public License.
# See the file LICENSE for details.

use CGI;

# The default size of each cell in the matrix, in pixels.
$cellsize=10;

# The pixels between each cell, needed to distinguish multiple slots.
$padding=1;

# The maximum number of users with distinct colors to show.
$color_max=10;

my $cgi = CGI->new();

my $sort_param = $cgi->param("sort");
if( defined $sort_param && ("$sort_param" eq "machine" || "$sort_param" eq "state" || "$sort_param" eq "user") ) {
	# ok
} else {
	$sort_param = "machine";
}

my $show_param = $cgi->param("show");
if( defined $show_param && ("$show_param" eq "user" || "$show_param" eq "state")) {
	# ok
} else {
	$show_param = "user";
}

my $size_param = $cgi->param("size");
if(defined $size_param && (int($size_param)>1 || int($size_param)<=100)) {
	$cellsize = int($size_param);
} else {
	$size_param = $cellsize;
}

my $scale_param = $cgi->param("scale");
if(defined $scale_param && ( $scale_param eq "none" || $scale_param eq "cores"  || $scale_param eq "memory" )) {
	# ok
} else {
	$scale_param = "cores";
}

sub compare_machine_cores {
	my ($x,$x,$acores,$x) = split "\t", $a;
	my ($x,$x,$bcores,$x) = split "\t", $b;

	return $acores <=> $bcores;
}

sub compare_machine_memory {
        my ($x,$x,$x,$amemory) = split "\t", $a;
        my ($x,$x,$x,$bmemory) = split "\t", $b;

        return $amemory <=> $bmemory;
}


# A function to sort all of the slots by machine name, and then
# by slot ID.  This is a bit complex because slot names may
# have the following forms:
#   machine.cse.nd.edu
#   slot#.cse.nd.edu

sub compare_machine_name {
	my ($slot_a, $machine_a) = split(/@/,$a);
	my ($slot_b, $machine_b) = split(/@/,$b);

	if(!defined $machine_a) {
		$machine_a = $slot_a;
		$slot_a = "slot1";
	}

	if(!defined $machine_b) {
		$machine_b = $slot_b;
		$slot_b = "slot1";
	}

	if($machine_a eq $machine_b) {
		my $num_a = substr($slot_a,4);
		my $num_b = substr($slot_b,4);
		return $num_a cmp $num_b;
	} else {
		return $machine_a cmp $machine_b;
	}
}

# Compare lines by state, then by machine name.

sub compare_state {
    my @aparts = split "\t", $a;
    my @bparts = split "\t", $b;
	if($aparts[1] eq $bparts[1]) {
		return compare_machine_name($a,$b);
	} else {
		return $aparts[1] cmp $bparts[1];
	}
}

# Compare lines by state, then by user.

sub compare_user {
    my @aparts = split "\t", $a;
    my @bparts = split "\t", $b;
    if($aparts[1] eq "Claimed" && $bparts[1] eq "Claimed") {
	if($aparts[4] eq $bparts[4]) {
	    return compare_machine_name($a,$b);
	} else {
	    return $color_index_of_user{$aparts[4]} <=> $color_index_of_user{$bparts[4]};
	}
    } else {
	return $aparts[1] cmp $bparts[1];
    }

}

# Slurp the entire file into an array.

open(FILE, "/tmp/condor.data/states.txt") or die("unable to open file");
@data = <FILE>;
close(FILE);

# First pass: sum up resources used by each user

foreach $line (@data) {
       	chomp $line;
	($name,$state,$cores,$memory,$user) = split "\t", $line;

	next if($cores==0);

       	if($state eq "Claimed") {
		$cores_by_user{$user}+=$cores;
		$memory_by_user{$user}+=$memory;
		$slots_by_user{$user}++;
       	}

	$cores_by_state{$state}+=$cores;
	$memory_by_state{$state}+=$memory;
	$slots_by_state{$state}++;

	$cores_by_state{"Total"}+=$cores;
	$memory_by_state{"Total"}+=$memory;
	$slots_by_state{"Total"}++;
}


# Pick the top N users and select a color for each.

@users = sort { $cores_by_user{$b} <=> $cores_by_user{$a} } keys %cores_by_user;

for($i=0;$i<=$#users;$i++) {
	$color_index_of_user{$users[$i]} = $i < $color_max ? $i : $color_max;
}

# Emit the page header and the CSS.

print <<EOF
Content-type: text/html\n\n

<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\" \"http://www.w3.org/TR/html4/strict.dtd\">
<html>
<head>
<meta charset=\"UTF-8\">
<meta http-equiv=\"refresh\" content=\"60\">
<title>Condor Matrix Display</title>
<style type=\"text/css\">

body {
  background: \#000000;
  color: \#ffffff;
}

.key {
  border:1px solid;
  font-family:arial;
  padding:5px;
  text-align: center;
}

.usertable {
    text-align: left;
    font-size: 125%;
}

.optiontable {
    font-size: 125%;
    margin-left: auto;
    margin-right: auto;
    text-align: right;
}

.matrix {
  border:1px solid;
}

.b { float:left;width:${cellsize}px;height:${cellsize}px;margin:${padding}px; }

a.u   { background-color:\#484; }
a.m   { background-color:\#006; }
a.c   { background-color:\#00F; }
a.p   { background-color:\#F60; }
a.o   { background-color:\#800; }

a.u0  { background-color:\#00F; }
a.u1  { background-color:\#0F0; }
a.u2  { background-color:\#FF0; }
a.u3  { background-color:\#F0F; }
a.u4  { background-color:\#0FF; }
a.u5  { background-color:\#F00; }
a.u6  { background-color:\#FFF; }
a.u7  { background-color:\#AAA; }
a.u8  { background-color:\#888; }
a.u9  { background-color:\#444; }
a.u10 { background-color:\#111; }
</style>
</head>
<body>
EOF
;

# Emit the key side of the display:

print "<table>\n";
print "<tr>\n";
print "<td class=key valign=top>\n";

print "<h1>Notre Dame<br>Condor Status</h1>";
print "<table class=usertable>\n";
print "<tr><td><td><th align=right>Slots<th align=right>Cores\n";

# For each user, emit the resources in use.

if( $show_param eq "user") {
	foreach $user ( @users ) {
		next if($user eq "");
		$i = $color_index_of_user{$user};
		$memory = int($memory_by_user{$user}/1024);
		$cores = $cores_by_user{$user};
		$slots = $slots_by_user{$user};
		print "<tr><td><a class=\"u${i} b\" style=\"width:20px; height:20px;\"></a><td>$user<td align=right>$slots<td align=right>$cores\n";
	}

	print "<tr><td>&nbsp;\n";
}

# For each machine state, emit the resources in use.

foreach $state ( "Claimed", "Unclaimed", "Matched", "Preempting", "Owner", "Total" ) {
	next if($show_param eq "user" && $state eq "Claimed");
	$class = lc(substr($state,0,1));
	$memory = int($memory_by_state{$state}/1024);
	$cores = $cores_by_state{$state};
	$slots = $slots_by_state{$state};
	print "<tr><td><a class=\"$class b\" style=\"width:20px; height:20px;\"></a><td>$state<td align=right>$slots<td align=right>$cores\n";
}
print "</table>\n";


$bigger = $size_param + 2;
$smaller = $size_param -2;

print "<h2>Display Options</h2>\n";
print <<EOF
<table class=optiontable>
<tr>
<td>Sort:
<td><a href=?sort=user&show=${show_param}&size=${size_param}&scale=${scale_param}>users</a>
<td><a href=?sort=machine&show=${show_param}&size=${size_param}&scale=${scale_param}>machines</a>
<tr>
<td>Show:
<td><a href=?sort=${sort_param}&show=user&size=${size_param}&scale=${scale_param}>users</a>
<td><a href=?sort=${sort_param}&show=state&size=${size_param}&scale=${scale_param}>states</a>
<tr>
<td>Size:
<td><a href=?sort=${sort_param}&show=${show_param}&size=${bigger}&scale=${scale_param}>bigger</a>
<td><a href=?sort=${sort_param}&show=${show_param}&size=${smaller}&scale=${scale_param}>smaller</a>
<tr>
<td>Scale:
<td><a href=?sort=${sort_param}&show=${show_param}&size=${size_param}&scale=none>none</a>
<tr>
<td>
<td><a href=?sort=${sort_param}&show=${show_param}&size=${size_param}&scale=cores>cores</a>
<tr>
<td>
<td><a href=?sort=${sort_param}&show=${show_param}&size=${size_param}&scale=memory>memory</a>
</table>

<h2><a href=http://condor.cse.nd.edu>http://condor.cse.nd.edu</a></h2>
EOF
;



# Second pass through the data: emit a box for each slot in the system

print "<td class=matrix>\n";

if($sort_param eq "state" || $sort_param eq "user") {
	@data = sort compare_user @data;
} else {
	@data = sort compare_machine_name @data;
}

foreach $line (@data) {
        	chomp $line;
		($name,$state,$cores,$memory,$user) = split "\t", $line;

		next if($cores==0);

		if($state eq "Unclaimed") {
			$class="u";
        	} elsif($state eq "Claimed") {
			if($show_param eq "user") {
				$color_index = $color_index_of_user{$user};
				$class="u$color_index";
			} else {
				$class="c";
			}
        	} elsif($state eq "Matched") {
			$class="m";
        	} elsif($state eq "Preempting") {
			$class="p";
		} else {
			$class="o";
        	}

		$tooltip=sprintf("$name ($state) $cores core%s %3.1lf GB",$cores > 1 ? "s" : "", $memory/1024.0);


		# Note that we add padding to cells of more than one unit,
		# to match up with the inter-cell padding of adjacent cells.

		if($scale_param eq "cores") {
			$width = $cellsize + ($cores-1)*($cellsize+${padding}*2);
			$height = $cellsize;
		} elsif($scale_param eq "memory") {
			$width = $cellsize + (int(${memory}/1024)*(($cellsize+${padding}*2)));
			$height = $cellsize;
		} else {
			$width = $height = $cellsize;
		}

        	print "<a class=\"$class b\" style=\"height: ${height}px; width:${width}px;\" href=\"#\" title=\"$tooltip\"></a>\n";
}

print "</table>\n";
print "</body>\n";
print "</html>\n";
