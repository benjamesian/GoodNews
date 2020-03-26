# Configure and enable ufw

package {'ufw':
  ensure => installed,
}

service {'ufw.service':
  ensure    => running,
  enable    => true,
}

exec {'ssh':
  command => 'ufw allow proto tcp from any to any port 22',
  path    => '/usr/sbin:/usr/bin:/sbin:/bin',
  require => Service['ufw.service'],
}

exec {'http':
  command => 'ufw allow proto tcp from any to any port 80',
  path    => '/usr/sbin:/usr/bin:/sbin:/bin',
  require => Service['ufw.service'],
}

exec {'https':
  command => 'ufw allow proto tcp from any to any port 443',
  path    => '/usr/sbin:/usr/bin:/sbin:/bin',
  require => Service['ufw.service'],
}

exec {'django':
  command => 'ufw allow proto tcp from any to any port 5000',
  path    => '/usr/sbin:/usr/bin:/sbin:/bin',
  require => Service['ufw.service'],
}

exec {'enable':
  command => 'ufw enable',
  path    => '/usr/sbin:/usr/bin:/sbin:/bin',
  require => [Exec['ssh'], Exec['http'], Exec['https'], Exec['django']],
  notify  => Service['ufw.service'],
}
