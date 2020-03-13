# Configure the scraping service

service {'scraping.service':
  ensure    => stopped,
  enable    => false,
  require   => File['scraping.service'],
  subscribe => Exec['reload'],
}

service {'scraping.timer':
  ensure    => running,
  enable    => true,
  require   => [File['scraping.timer'], Service['scraping.service']],
  subscribe => Exec['reload'],
}

file {'scraping.service':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/scraping.service',
  source => '/data/current/etc/systemd/system/scraping.service',
  notify => Exec['reload'],
}

file {'scraping.timer':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/scraping.timer',
  source => '/data/current/etc/systemd/system/scraping.timer',
  notify => Exec['reload'],
}

exec {'reload':
  command => 'systemctl daemon-reload',
  path    => '/usr/bin:/bin',
}

exec {'restart':
  command => 'systemctl restart scraping.timer scraping.service',
  path    => '/usr/bin:/bin',
  require => [Exec['reload'], Service['scraping.timer'], Service['scraping.service']],
}
