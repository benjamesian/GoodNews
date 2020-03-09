# Set up the scraping service on a server

service {'scraping.timer':
  ensure    => running,
  enable    => true,
  provider  => systemd,
  require   => File['scraping.timer'],
  subscribe => Exec['daemon-reload'],
}

service {'scraping.service':
  ensure   => stopped,
  enable   => false,
  provider => systemd,
  requires => Service['scraping.timer']
}

file {'scraping.timer':
  ensure  => file,
  mode    => '0644',
  owner   => 'root',
  group   => 'root',
  notify  => Exec['daemon-reload'],
  require => Exec['stop timer'],
  path    => '/etc/systemd/system/scraping.timer',
  source  => '/data/current/etc/systemd/system/scraping.timer',
}

file {'scraping.service':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  # require => Service['scraping.service'],
  before => File['scraping.timer'],
  path   => '/etc/systemd/system/scraping.service',
  source => '/data/current/etc/systemd/system/scraping.service',
}


exec {'stop timer':
  command     => 'systemctl stop scraping.timer',
  path        => '/usr/bin:/bin',
  refreshonly => false,
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
